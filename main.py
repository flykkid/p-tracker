# -*- coding: utf-8 -*-
from fastapi import FastAPI, Form, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from database import engine, SessionLocal
from models import Base, Pedido, RegistroEntrega, Cliente
from datetime import datetime
import json, re, time, hashlib

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Go Shop Tracking Pro", version="3.0")
app.add_middleware(SessionMiddleware, secret_key="GoShop2024Secure!")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

rate_limit = {}
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host
    now = time.time()
    if ip in rate_limit:
        if now - rate_limit[ip]["time"] < 1:
            rate_limit[ip]["count"] += 1
            if rate_limit[ip]["count"] > 30: raise HTTPException(status_code=429)
        else: rate_limit[ip] = {"time": now, "count": 1}
    else: rate_limit[ip] = {"time": now, "count": 1}
    return await call_next(request)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

def sanitize(v: str) -> str:
    for d in ["SELECT","DROP","DELETE","INSERT","UPDATE","UNION","--",";","<script"]:
        if d.upper() in v.upper(): raise HTTPException(status_code=400)
    return re.sub(r'[<>\"\']', '', v)

def hash_pw(pw: str) -> str: return hashlib.sha256(pw.encode()).hexdigest()

# WebSockets
websockets = {}
admin_sockets = []

@app.websocket("/ws/{codigo}")
async def ws_endpoint(ws: WebSocket, codigo: str):
    await ws.accept()
    websockets[codigo] = ws
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        websockets.pop(codigo, None)

@app.websocket("/ws-admin")
async def ws_admin(ws: WebSocket):
    await ws.accept()
    admin_sockets.append(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        admin_sockets.remove(ws)

async def notificar_cliente(codigo: str, msg: dict):
    if codigo in websockets:
        try: await websockets[codigo].send_text(json.dumps(msg))
        except: websockets.pop(codigo, None)

async def notificar_admin(msg: dict):
    for ws in admin_sockets:
        try: await ws.send_text(json.dumps(msg))
        except: admin_sockets.remove(ws)

# ============ PUBLICO ============
@app.get("/")
def home():
    return HTMLResponse(open("templates/home.html", encoding="utf-8").read())

@app.get("/login")
def login_page():
    return HTMLResponse(open("templates/login.html", encoding="utf-8").read())

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    cliente = db.query(Cliente).filter(Cliente.email == username).first()
    db.close()
    if cliente and cliente.password == hash_pw(password):
        request.session["cliente_id"] = cliente.id
        request.session["cliente_nombre"] = cliente.nombre
        return RedirectResponse(url="/mis-pedidos", status_code=303)
    if username == "admin" and password == "1234":
        request.session["admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    html = open("templates/login.html", encoding="utf-8").read()
    return HTMLResponse(html.replace("<!--ERROR-->", '<div class="error">Credenciales incorrectas</div>'))

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/mis-pedidos")
def mis_pedidos(request: Request):
    if not request.session.get("cliente_id"): return RedirectResponse(url="/login", status_code=303)
    db = SessionLocal()
    pedidos = db.query(Pedido).filter(Pedido.cliente_id == request.session["cliente_id"], Pedido.confirmado != "confirmado").all()
    db.close()
    rows = ""
    for p in pedidos:
        rows += f'<tr><td>#{p.codigo}</td><td><span class="estado">{p.estado}</span></td><td>{p.tipo_envio}</td><td>{p.destino}</td><td><a href="/buscar?codigo={p.codigo}" class="btn-ver">Ver tracking</a></td></tr>'
    if not rows: rows = '<tr><td colspan="5" style="text-align:center;padding:30px;">No tienes pedidos activos</td></tr>'
    html = open("templates/mis_pedidos.html", encoding="utf-8").read()
    return HTMLResponse(html.replace("{FILAS}", rows).replace("{NOMBRE}", request.session.get("cliente_nombre","")))

@app.get("/buscar")
def buscar(codigo: str):
    codigo = sanitize(codigo)
    db = SessionLocal()
    pedido = db.query(Pedido).filter(Pedido.codigo == codigo).first()
    db.close()
    if not pedido:
        return HTMLResponse(open("templates/no_encontrado.html", encoding="utf-8").read().replace("{CODIGO}", codigo))
    
    html = open("templates/tracking.html", encoding="utf-8").read()
    
    if pedido.tipo_envio == "Lima":
        etapas = ["Validado", "Alistado", "En transito", "En almacen"]
        descs = ["Verificando tu pago","Estamos preparando tu pedido","Tu pedido viaja al almacen","Listo en " + pedido.destino]
        iconos = ["🏢","📦","🚛","🏁"]
    else:
        etapas = ["Validado", "Alistado", "En transito", "En agencia"]
        descs = ["Verificando tu pago","Estamos preparando tu pedido","Tu pedido viaja a la agencia","Listo en agencia"]
        iconos = ["🏢","📦","🚛","🏁"]
    
    estado_idx = etapas.index(pedido.estado) if pedido.estado in etapas else 0
    
    steps_html = ""
    for i in range(4):
        if i < estado_idx:
            clase, icono_extra = "completed", ""
        elif i == estado_idx:
            clase, icono_extra = "active", "pulse"
        else:
            clase, icono_extra = "", ""
        
        barra = ""
        if i < 3:
            if i < estado_idx: barra_clase = "bar-completed"
            elif i == estado_idx: barra_clase = "bar-active"
            else: barra_clase = ""
            barra = f'<div class="connector {barra_clase}"></div>'
        
        badge = '<span class="badge-actual">Ahora</span>' if i == estado_idx else ''
        
        steps_html += f'''
        <div class="step {clase} {icono_extra}">
            <div class="step-circle">{iconos[i]}</div>
            <div class="step-info">
                <h4>{etapas[i]}</h4>
                <p>{descs[i]}</p>
                {badge}
            </div>
            {barra}
        </div>'''
    
    html = html.replace("{{STEPS}}", steps_html)
    html = html.replace("{{CODIGO}}", pedido.codigo)
    html = html.replace("{{CLIENTE}}", pedido.cliente)
    html = html.replace("{{TIPO}}", pedido.tipo_envio)
    html = html.replace("{{DESTINO}}", pedido.destino)
    html = html.replace("{{ESTADO}}", pedido.estado)
    
    if pedido.confirmado != "confirmado":
        html = html.replace("<!--CONFIRMAR-->", 
            f'<div class="confirm-section"><button onclick="confirmar()" class="btn-confirm">? Confirmar Recepcion</button><p class="confirm-hint">Presiona cuando hayas recibido tu pedido</p></div>')
    else:
        html = html.replace("<!--CONFIRMAR-->", 
            '<div class="confirm-section"><div class="confirmed-msg">? Recepcion confirmada<br><span>Gracias por confiar en Go Shop</span></div></div>')
    
    html = html.replace("<!--WS_SCRIPT-->", 
        f'<script>new WebSocket("ws://127.0.0.1:8000/ws/{codigo}").onmessage=e=>{{var d=JSON.parse(e.data);if(d.tipo=="actualizacion"||d.tipo=="confirmado")location.reload();}};function confirmar(){{fetch("/confirmar/{codigo}",{{method:"POST"}}).then(r=>r.json()).then(d=>{{if(d.ok)location.reload();}})}}</script>')
    
    return HTMLResponse(html)

@app.post("/confirmar/{codigo}")
async def confirmar(codigo: str):
    db = SessionLocal()
    p = db.query(Pedido).filter(Pedido.codigo == codigo).first()
    if p and p.confirmado != "confirmado":
        p.confirmado = "confirmado"
        p.fecha_entrega = datetime.utcnow()
        db.add(RegistroEntrega(codigo_pedido=codigo, cliente=p.cliente, tipo_envio=p.tipo_envio, destino=p.destino, fecha_confirmacion=datetime.utcnow()))
        db.commit()
        await notificar_cliente(codigo, {"tipo": "confirmado"})
        await notificar_admin({"tipo": "recargar"})
        db.close()
        return {"ok": True}
    db.close()
    return {"ok": False}

# ============ ADMIN ============
@app.get("/admin")
def admin(request: Request):
    if not request.session.get("admin"): return RedirectResponse(url="/login", status_code=303)
    
    db = SessionLocal()
    pedidos = db.query(Pedido).filter(Pedido.confirmado != "confirmado").order_by(Pedido.id.desc()).all()
    historial = db.query(RegistroEntrega).order_by(RegistroEntrega.fecha_confirmacion.desc()).limit(50).all()
    clientes = db.query(Cliente).all()
    
    total = len(pedidos)
    validados = len([p for p in pedidos if p.estado == "Validado"])
    alistados = len([p for p in pedidos if p.estado == "Alistado"])
    en_transito = len([p for p in pedidos if p.estado == "En transito"])
    en_destino = len([p for p in pedidos if p.estado in ["En almacen", "En agencia"]])
    lima = len([p for p in pedidos if p.tipo_envio == "Lima"])
    agencia = len([p for p in pedidos if p.tipo_envio == "Agencia"])
    confirmados_hoy = len([h for h in historial if h.fecha_confirmacion.date() == datetime.utcnow().date()])
    db.close()
    
    html = open("templates/admin.html", encoding="utf-8").read()
    for k, v in {"{TOTAL}":total,"{VALIDADOS}":validados,"{ALISTADOS}":alistados,"{EN_TRANSITO}":en_transito,"{EN_DESTINO}":en_destino,"{LIMA}":lima,"{AGENCIA}":agencia,"{CONFIRMADOS_HOY}":confirmados_hoy,"{TOTAL_HISTORIAL}":len(historial)}.items():
        html = html.replace(k, str(v))
    
    # Pedidos
    rows = ""
    for p in pedidos:
        if p.estado == "Validado": ec = "e-validado"
        elif p.estado == "Alistado": ec = "e-alistado"
        elif p.estado == "En transito": ec = "e-transito"
        else: ec = "e-destino"
        rows += f'<tr><td><strong>#{p.codigo}</strong></td><td>{p.cliente}</td><td>{p.tipo_envio}</td><td>{p.destino}</td><td><span class="estado {ec}">{p.estado}</span></td>'
        rows += f'<td><form action="/actualizar" method="post"><input type="hidden" name="codigo" value="{p.codigo}"><select name="estado" class="sel-sm">'
        rows += '<option>Validado</option><option>Alistado</option><option>En transito</option>'
        rows += '<option>En almacen</option>' if p.tipo_envio == "Lima" else '<option>En agencia</option>'
        rows += f'</select><button class="btn-o btn-sm">Actualizar</button></form></td></tr>'
    html = html.replace("{PEDIDOS_ROWS}", rows if rows else '<tr><td colspan="6" class="empty">Sin pedidos activos</td></tr>')
    
    # Historial
    hrows = ""
    for h in historial:
        hrows += f'<tr><td>#{h.codigo_pedido}</td><td>{h.cliente}</td><td>{h.tipo_envio}</td><td>{h.destino}</td><td>{h.fecha_confirmacion.strftime("%d/%m/%Y %H:%M")}</td></tr>'
    html = html.replace("{HISTORIAL_ROWS}", hrows if hrows else '<tr><td colspan="5" class="empty">Sin entregas</td></tr>')
    
    # Clientes
    copts = "".join(f'<option value="{c.id}">{c.nombre} ({c.email})</option>' for c in clientes)
    html = html.replace("{CLIENTES_OPTIONS}", copts)
    crows = "".join(f'<tr><td>{c.nombre}</td><td>{c.email}</td><td>{c.telefono}</td></tr>' for c in clientes)
    html = html.replace("{CLIENTES_ROWS}", crows if crows else '<tr><td colspan="3" class="empty">Sin clientes</td></tr>')
    
    return HTMLResponse(html)

@app.post("/admin/crear-cliente")
def crear_cliente(nombre: str = Form(...), email: str = Form(...), password: str = Form(...), telefono: str = Form("")):
    db = SessionLocal()
    if db.query(Cliente).filter(Cliente.email == email).first():
        db.close(); return HTMLResponse('<script>alert("Email ya existe");location.href="/admin";</script>')
    db.add(Cliente(nombre=nombre, email=email, password=hash_pw(password), telefono=telefono))
    db.commit(); db.close()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/crear")
def crear_pedido(codigo: str = Form(...), cliente: str = Form(...), tipo_envio: str = Form("Lima"), destino: str = Form("San Luis"), cliente_id: str = Form("")):
    codigo = sanitize(codigo); cliente = sanitize(cliente)
    db = SessionLocal()
    if db.query(Pedido).filter(Pedido.codigo == codigo).first():
        db.close(); return HTMLResponse('<script>alert("Codigo ya existe");location.href="/admin";</script>')
    cid = int(cliente_id) if cliente_id else None
    db.add(Pedido(codigo=codigo, cliente=cliente, tipo_envio=tipo_envio, destino=destino, estado="Validado", confirmado="pendiente", cliente_id=cid, fecha_creacion=datetime.utcnow()))
    db.commit(); db.close()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/actualizar")
async def actualizar(codigo: str = Form(...), estado: str = Form(...)):
    db = SessionLocal()
    p = db.query(Pedido).filter(Pedido.codigo == codigo).first()
    if p:
        p.estado = estado; db.commit()
        await notificar_cliente(codigo, {"tipo": "actualizacion", "estado": estado})
    db.close()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/eliminar")
def eliminar(codigo: str = Form(...)):
    db = SessionLocal()
    p = db.query(Pedido).filter(Pedido.codigo == codigo).first()
    if p: db.delete(p); db.commit()
    db.close()
    return RedirectResponse(url="/admin", status_code=303)

