from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.services.pedido_service import PedidoService

router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@router.get("/buscar")
def buscar(request: Request, codigo: str, db: Session = Depends(get_db)):
    service = PedidoService(db)
    pedido = service.get_by_codigo(codigo)
    
    if not pedido:
        return HTMLResponse("""
        <h1>Pedido no encontrado</h1>
        <a href="/">Volver</a>
        """)
    
    return templates.TemplateResponse(
        "tracking.html",
        {"request": request, "pedido": pedido}
    )
