from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# SESIONES
app.add_middleware(
    SessionMiddleware,
    secret_key="supersecretkey"
)

# PEDIDOS
pedidos = {
    "488304882948831-VLID": {
        "cliente": "KAM KAM ANGEL",
        "estado": "En preparación"
    }
}

# =========================
# LOGIN
# =========================

@app.get("/login", response_class=HTMLResponse)
def login_page():

    return """

<html>

<head>
<title>Login Admin</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
background:#0b0b0b;
font-family:Arial;
color:white;
display:flex;
justify-content:center;
align-items:center;
height:100vh;
">

<div style="
background:#151515;
padding:40px;
border-radius:20px;
width:300px;
text-align:center;
">

<h1>🔒 Admin</h1>

<form action="/login" method="post">

<input
type="text"
name="username"
placeholder="Usuario"
style="
width:100%;
padding:15px;
margin-top:15px;
border:none;
border-radius:10px;
"
>

<input
type="password"
name="password"
placeholder="Contraseña"
style="
width:100%;
padding:15px;
margin-top:15px;
border:none;
border-radius:10px;
"
>

<button
style="
margin-top:20px;
width:100%;
padding:15px;
background:#00d000;
color:black;
font-weight:bold;
border:none;
border-radius:10px;
cursor:pointer;
"
>
Entrar
</button>

</form>

</div>

</body>

</html>

"""

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
    <h1>❌ Login incorrecto</h1>
    <a href="/login">Volver</a>
    """)

# =========================
# HOME
# =========================

@app.get("/", response_class=HTMLResponse)
def inicio():

    return """

<html>

<head>

<title>GOSHOP</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>

body{
    background:#001500;
    font-family:Arial;
    color:white;
    margin:0;
    padding:20px;
}

.logo{
    text-align:center;
    margin-top:30px;
}

.logo h1{
    font-size:60px;
    margin:0;
    font-weight:bold;
}

.logo h2{
    color:#00ff2a;
    margin-top:10px;
    letter-spacing:5px;
}

.subtitle{
    text-align:center;
    color:#bdbdbd;
    margin-top:20px;
    font-size:22px;
}

.search-box{
    display:flex;
    gap:10px;
    margin-top:40px;
}

.search-box input{
    flex:1;
    padding:20px;
    border-radius:20px;
    border:1px solid #333;
    background:#0c0c0c;
    color:white;
    font-size:22px;
}

.search-box button{
    width:160px;
    border:none;
    border-radius:20px;
    background:#00e000;
    color:black;
    font-size:25px;
    font-weight:bold;
    cursor:pointer;
}

.admin-btn{
    display:block;
    text-align:center;
    margin-top:30px;
    color:#00ff2a;
    text-decoration:none;
    font-size:20px;
}

</style>

</head>

<body>

<div class="logo">

<h1>GOSHOP</h1>
<h2>TRACKING STATE</h2>

</div>

<div class="subtitle">
Ingresa tu número de pedido para ver el estado en tiempo real.
</div>

<form action="/buscar">

<div class="search-box">

<input
name="codigo"
placeholder="Ingresa tu código"
>

<button type="submit">
Buscar
</button>

</div>

</form>

<a class="admin-btn" href="/login">
⚙️ Panel Admin
</a>

</body>

</html>

"""

# =========================
# BUSCAR
# =========================

@app.get("/buscar", response_class=HTMLResponse)
def buscar(codigo: str):

    if codigo not in pedidos:

        return """

<body style='background:black;color:white;font-family:Arial;padding:40px;'>

<h1>❌ Pedido no encontrado</h1>

<a href="/" style="color:#00ff2a;">
← Volver
</a>

</body>

"""

    pedido = pedidos[codigo]

    return f"""

<html>

<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
background:#001500;
font-family:Arial;
color:white;
padding:20px;
">

<div style="
background:#002900;
border-radius:30px;
overflow:hidden;
border:2px solid #00aa00;
">

<div style="
background:#00d000;
color:black;
padding:30px;
">

<h1>Pedido #{codigo}</h1>
<h2>{pedido['cliente']}</h2>

</div>

<div style="padding:30px;">

<div style="margin-bottom:40px;">
<h2 style="color:#00ff2a;">✔ En validación</h2>
<p>Revisando tu pedido</p>
</div>

<div style="margin-bottom:40px;">
<h2 style="color:#00ff2a;">✔ Validado</h2>
<p>Pedido confirmado</p>
</div>

<div style="margin-bottom:40px;">
<h2 style="color:#00ff2a;">⦿ {pedido['estado']}</h2>
<p>Preparando tu pedido</p>

<div style="
background:#00ff2a;
color:black;
padding:10px 20px;
border-radius:30px;
display:inline-block;
font-weight:bold;
margin-top:10px;
">
Estado actual
</div>

</div>

<div style="opacity:0.4;margin-bottom:40px;">
<h2>Enviado por agencia</h2>
<p>Ya lo dejamos en agencia</p>
</div>

<div style="opacity:0.4;">
<h2>Entregado</h2>
<p>Pedido recibido con éxito</p>
</div>

</div>

</div>

<br>

<a href="/" style="color:#00ff2a;">
← Buscar otro pedido
</a>

</body>

</html>

"""

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

<body style='background:#001500;font-family:Arial;color:white;padding:30px;'>

<h1>⚙️ PANEL ADMIN</h1>

<form action='/crear' method='post'>

<input
name='codigo'
placeholder='Código'
style='padding:15px;border-radius:10px;border:none;'
>

<input
name='cliente'
placeholder='Cliente'
style='padding:15px;border-radius:10px;border:none;'
>

<button style='
padding:15px;
background:#00d000;
border:none;
border-radius:10px;
font-weight:bold;
'>
Crear Pedido
</button>

</form>

<hr>

"""

    for codigo, pedido in pedidos.items():

        html += f"""

<div style='
background:#002900;
padding:20px;
margin-top:20px;
border-radius:20px;
'>

<h2>{codigo}</h2>

<p>{pedido['cliente']}</p>

<p>{pedido['estado']}</p>

<form action='/actualizar' method='post'>

<input type='hidden' name='codigo' value='{codigo}'>

<select
name='estado'
style='padding:10px;border-radius:10px;'
>
<option>En preparación</option>
<option>Enviado por agencia</option>
<option>Entregado</option>
</select>

<button style='
padding:10px;
background:#00d000;
border:none;
border-radius:10px;
margin-left:10px;
'>
Actualizar
</button>

</form>

<form action='/eliminar' method='post'>

<input type='hidden' name='codigo' value='{codigo}'>

<button style='
background:red;
color:white;
margin-top:10px;
padding:10px;
border:none;
border-radius:10px;
'>
Eliminar
</button>

</form>

</div>

"""

    html += """

<br><br>

<a href='/logout' style='color:red;font-size:20px;'>
Cerrar sesión
</a>

</body>

"""

    return html

# =========================
# CREAR PEDIDO
# =========================

@app.post("/crear")
def crear(
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
        "estado": "En preparación"
    }

    return RedirectResponse(
        url="/admin",
        status_code=303
    )

# =========================
# ACTUALIZAR
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
# ELIMINAR
# =========================

@app.post("/eliminar")
def eliminar(
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

# =========================
# LOGOUT
# =========================

@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=303
    )