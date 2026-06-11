from sqlalchemy.orm import Session
from models import Pedido

class PedidoService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self):
        return self.db.query(Pedido).all()
    
    def get_by_codigo(self, codigo: str):
        return self.db.query(Pedido).filter(Pedido.codigo == codigo).first()
    
    def create(self, codigo: str, cliente: str):
        pedido = Pedido(
            codigo=codigo,
            cliente=cliente,
            estado="En validación"
        )
        self.db.add(pedido)
        self.db.commit()
        return pedido
    
    def update_estado(self, codigo: str, estado: str):
        pedido = self.get_by_codigo(codigo)
        if pedido:
            pedido.estado = estado
            self.db.commit()
        return pedido
    
    def delete(self, codigo: str):
        pedido = self.get_by_codigo(codigo)
        if pedido:
            self.db.delete(pedido)
            self.db.commit()
            return True
        return False
