from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from config import settings

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == settings.admin_username and password == settings.admin_password:
        request.session["admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": "Usuario o contraseña incorrectos"
        }
    )

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
