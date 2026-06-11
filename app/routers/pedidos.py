from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.dependencies import get_db, verificar_admin
from app.services.pedido_service import PedidoService

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/")
def admin_panel(request: Request, db: Session = Depends(get_db)):
    verificar_admin(request)
    service = PedidoService(db)
    pedidos = service.get_all()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "pedidos": pedidos}
    )

@router.post("/crear")
def crear_pedido(
    request: Request,
    codigo: str = Form(...),
    cliente: str = Form(...),
    db: Session = Depends(get_db)
):
    verificar_admin(request)
    service = PedidoService(db)
    service.create(codigo, cliente)
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/actualizar")
def actualizar(
    request: Request,
    codigo: str = Form(...),
    estado: str = Form(...),
    db: Session = Depends(get_db)
):
    verificar_admin(request)
    service = PedidoService(db)
    service.update_estado(codigo, estado)
    return RedirectResponse(url="/admin", status_code=303)

@router.post("/eliminar")
def eliminar(
    request: Request,
    codigo: str = Form(...),
    db: Session = Depends(get_db)
):
    verificar_admin(request)
    service = PedidoService(db)
    service.delete(codigo)
    return RedirectResponse(url="/admin", status_code=303)
