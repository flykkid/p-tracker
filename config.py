from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "supersecretkey"
    database_url: str = "sqlite:///./pedidos.db"
    admin_username: str = "admin"
    admin_password: str = "1234"
    
    class Config:
        env_file = ".env"

settings = Settings()
