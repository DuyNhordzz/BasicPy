import os

# Cấu trúc dự án và nội dung file
project_structure = {
    "requirements.txt": """fastapi
uvicorn
sqlalchemy
pymysql
python-dotenv
pydantic
passlib[bcrypt]
python-jose[cryptography]
""",
    ".env": """# Cấu hình Database (Mặc định cho XAMPP: user=root, pass=rỗng)
DATABASE_URL=mysql+pymysql://root:@localhost:3306/BizFlowDB
SECRET_KEY=bizflow_secret_key_2025
""",
    "main.py": """import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Fix lỗi ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database.session import engine
from app.domain.entities import models
from app.api.api_v1.api import api_router

# Tự động tạo bảng Database nếu chưa có
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BizFlow Backend API", version="1.0.0")

# Cấu hình CORS (Cho phép Frontend/Mobile gọi vào)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to BizFlow API", "docs": "/docs"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
    "app/__init__.py": "",
    "app/domain/__init__.py": "",
    "app/domain/entities/__init__.py": "",
    "app/domain/entities/models.py": """from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.session import Base
import enum

class UserRole(str, enum.Enum):
    OWNER = "Owner"
    EMPLOYEE = "Employee"
    ADMIN = "Admin"

class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    store_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    products = relationship("Product", back_populates="owner")

class Product(Base):
    __tablename__ = "Products"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    code = Column(String(20), nullable=True)
    name = Column(String(200), nullable=False)
    base_price = Column(Numeric(18, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(20), default="Cái")
    is_active = Column(Boolean, default=True)
    
    owner = relationship("User", back_populates="products")
""",
    "app/infrastructure/__init__.py": "",
    "app/infrastructure/database/__init__.py": "",
    "app/infrastructure/database/session.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Lấy connection string từ .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
    "app/api/__init__.py": "",
    "app/api/api_v1/__init__.py": "",
    "app/api/api_v1/api.py": """from fastapi import APIRouter
from app.api.api_v1.endpoints import products, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
""",
    "app/api/api_v1/endpoints/__init__.py": "",
    "app/api/api_v1/endpoints/products.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.domain.entities import models

router = APIRouter()

@router.get("/")
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@router.post("/")
def create_test_product(name: str, price: float, store_id: int, db: Session = Depends(get_db)):
    # API test nhanh để tạo sản phẩm
    new_product = models.Product(
        name=name, 
        base_price=price, 
        store_id=store_id,
        code=f"SP-{name[:3].upper()}"
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product
""",
    "app/api/api_v1/endpoints/auth.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.infrastructure.database.session import get_db
from app.domain.entities import models

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Demo login đơn giản (Chưa check hash pass để dễ test)
    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Trong thực tế phải check password hash
    return {
        "access_token": "fake-jwt-token-for-demo", 
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }
"""
}

def create_project():
    print(" Đang khởi tạo dự án BizFlow Backend...")
    current_dir = os.getcwd()
    
    for file_path, content in project_structure.items():
        full_path = os.path.join(current_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f" Đã tạo: {file_path}")


if __name__ == "__main__":
    create_project()