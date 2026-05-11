from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Pedido(Base):

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)

    codigo = Column(String, unique=True)

    cliente = Column(String)

    estado = Column(String)