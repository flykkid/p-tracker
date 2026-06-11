from fastapi import Request, HTTPException
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verificar_admin(request: Request):
    if not request.session.get("admin"):
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"}
        )
