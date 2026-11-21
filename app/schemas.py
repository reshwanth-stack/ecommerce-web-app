
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: str = ""
    stock: int = 10


class ProductResponse(ProductCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
