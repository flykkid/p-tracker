from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    telefono = Column(String, default="")

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, index=True)
    cliente = Column(String)
    cliente_id = Column(Integer, nullable=True)
    tipo_envio = Column(String, default="Lima")
    destino = Column(String, default="San Luis")
    estado = Column(String, default="Validado")
    confirmado = Column(String, default="pendiente")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)

class RegistroEntrega(Base):
    __tablename__ = "registros_entregas"
    id = Column(Integer, primary_key=True)
    codigo_pedido = Column(String, index=True)
    cliente = Column(String)
    tipo_envio = Column(String)
    destino = Column(String)
    fecha_confirmacion = Column(DateTime, default=datetime.utcnow)
