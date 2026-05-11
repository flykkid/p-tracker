from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import engine, SessionLocal
from models import Base, Pedido

# =========================
# CREAR TABLAS
# =========================

Base.metadata.create_all(bind=engine)

# =========================
# APP
# =========================

app = FastAPI()

# =========================
# SESIONES
# =========================

app.add_middleware(
    SessionMiddleware,
    secret_key="supersecretkey"
)

# =========================
# TEMPLATES
# =========================

templates = Jinja2Templates(directory="templates")

# =========================
# PEDIDOS TEMPORALES
# =========================

pedidos = {

    "1001": {
        "cliente": "Juan Perez",
        "estado": "Preparando"
    },

    "1002": {
        "cliente": "Maria Lopez",
        "estado": "En tránsito"
    },

    "1003": {
        "cliente": "Carlos Ruiz",
        "estado": "Listo para recoger"
    }

}

# =========================
# LOGIN PAGE
# =========================

@app.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )
# =========================
# LOGIN
# =========================

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):

    if username == "admin" and password == "1234":

        request.session["admin"] = True

        return RedirectResponse(
            url="/admin",
            status_code=303
        )

    return HTMLResponse("""

    <h1>❌ Usuario o contraseña incorrectos</h1>

    <a href="/login">Volver</a>

    """)

# =========================
# LOGOUT
# =========================

@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303
    )

# =========================
# HOME
# =========================

@app.get("/", response_class=HTMLResponse)
def inicio():

    return """

<html>

<head>

    <title>P TRACKER</title>

    <style>

        body{
            font-family:Arial;
            background:#f2f2f2;
            padding:50px;
        }

        .box{
            background:white;
            width:400px;
            margin:auto;
            padding:30px;
            border-radius:15px;
            box-shadow:0 0 15px rgba(0,0,0,0.1);
            text-align:center;
        }

        input{
            width:90%;
            padding:12px;
            font-size:18px;
            margin-top:20px;
            border-radius:10px;
            border:1px solid #ccc;
        }

        button{
            margin-top:20px;
            padding:12px 25px;
            background:#007bff;
            color:white;
            border:none;
            border-radius:10px;
            font-size:18px;
            cursor:pointer;
        }

    </style>

</head>

<body>

    <div class="box">

        <h1>📦 P TRACKER</h1>

        <form action="/buscar">

            <input
                type="text"
                name="codigo"
                placeholder="Ingrese código"
            >

            <br>

            <button type="submit">
                Buscar Pedido
            </button>

        </form>

        <br><br>

        <a href="/login">
            🔐 Panel Admin
        </a>

    </div>

</body>

</html>

"""

# =========================
# BUSCAR PEDIDO
# =========================

@app.get("/buscar", response_class=HTMLResponse)
def buscar(codigo: str):

    if codigo in pedidos:

        pedido = pedidos[codigo]

        color = "orange"

        if pedido["estado"] == "En tránsito":
            color = "blue"

        if pedido["estado"] == "Listo para recoger":
            color = "green"

        if pedido["estado"] == "Despachado":
            color = "gray"

        return f"""

<html>

<body style="font-family:Arial;background:#f2f2f2;padding:50px;">

    <div style="
        background:white;
        width:450px;
        margin:auto;
        padding:30px;
        border-radius:15px;
    ">

        <h1>📦 Pedido</h1>

        <p><b>Código:</b> {codigo}</p>

        <p><b>Cliente:</b> {pedido['cliente']}</p>

        <p style="
            color:{color};
            font-size:28px;
            font-weight:bold;
        ">
            {pedido['estado']}
        </p>

        <a href="/">← Volver</a>

    </div>

</body>

</html>

"""

    return """

<h1>❌ Pedido no encontrado</h1>

<a href="/">← Volver</a>

"""

# =========================
# NUEVO PEDIDO
# =========================

@app.get("/nuevo", response_class=HTMLResponse)
def nuevo_pedido(request: Request):

    if not request.session.get("admin"):

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return """

<html>

<body style="font-family:Arial;padding:40px;">

    <h1>➕ Nuevo Pedido</h1>

    <form action="/guardar" method="post">

        <input
            type="text"
            name="codigo"
            placeholder="Código"
        >

        <br><br>

        <input
            type="text"
            name="cliente"
            placeholder="Cliente"
        >

        <br><br>

        <button type="submit">
            Guardar Pedido
        </button>

    </form>

    <br>

    <a href="/admin">← Volver</a>

</body>

</html>

"""

# =========================
# GUARDAR PEDIDO
# =========================

@app.post("/guardar")
def guardar(
    request: Request,
    codigo: str = Form(...),
    cliente: str = Form(...)
):

    if not request.session.get("admin"):

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    pedidos[codigo] = {
        "cliente": cliente,
        "estado": "Preparando"
    }

    db = SessionLocal()

    nuevo = Pedido(
        codigo=codigo,
        cliente=cliente,
        estado="Preparando"
    )

    db.add(nuevo)
    db.commit()
    db.close()

    return RedirectResponse(
        url="/admin",
        status_code=303
    )

# =========================
# PANEL ADMIN
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):

    if not request.session.get("admin"):

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    html = """

<html>

<head>

    <title>Admin</title>

    <style>

        body{
            font-family:Arial;
            background:#f2f2f2;
            padding:40px;
        }

        .card{
            background:white;
            padding:20px;
            margin-bottom:20px;
            border-radius:10px;
        }

        select{
            padding:10px;
            font-size:16px;
        }

        button{
            padding:10px 20px;
            color:white;
            border:none;
            border-radius:5px;
            cursor:pointer;
            margin-top:10px;
        }

        .green{
            background:green;
        }

        .red{
            background:red;
        }

    </style>

</head>

<body>

    <h1>⚙️ Panel Administrador</h1>

    <a href="/nuevo">➕ Crear Pedido</a>

    <br><br>

    <a href="/logout">🚪 Cerrar Sesión</a>

    <hr>

"""

    for codigo, pedido in pedidos.items():

        html += f"""

    <div class="card">

        <h2>Pedido {codigo}</h2>

        <p><b>Cliente:</b> {pedido['cliente']}</p>

        <p><b>Estado actual:</b> {pedido['estado']}</p>

        <form action="/actualizar" method="post">

            <input type="hidden" name="codigo" value="{codigo}">

            <select name="estado">

                <option>Preparando</option>

                <option>En tránsito</option>

                <option>Listo para recoger</option>

                <option>Despachado</option>

            </select>

            <br>

            <button class="green" type="submit">
                Actualizar
            </button>

        </form>

        <form action="/borrar" method="post">

            <input type="hidden" name="codigo" value="{codigo}">

            <button class="red" type="submit">
                🗑️ Borrar Pedido
            </button>

        </form>

    </div>

"""

    html += """

</body>

</html>

"""

    return html

# =========================
# ACTUALIZAR PEDIDO
# =========================

@app.post("/actualizar")
def actualizar(
    request: Request,
    codigo: str = Form(...),
    estado: str = Form(...)
):

    if not request.session.get("admin"):

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    pedidos[codigo]["estado"] = estado

    return RedirectResponse(
        url="/admin",
        status_code=303
    )

# =========================
# BORRAR PEDIDO
# =========================

@app.post("/borrar")
def borrar(
    request: Request,
    codigo: str = Form(...)
):

    if not request.session.get("admin"):

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    if codigo in pedidos:
        del pedidos[codigo]

    return RedirectResponse(
        url="/admin",
        status_code=303
    )