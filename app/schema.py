from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class  UserCreate(BaseModel):
    first_name : str
    last_name : str
    email : EmailStr
    password : str
    is_admin : bool

class UserResponse(BaseModel):
    id : int
    first_name : str
    last_name : str
    email : EmailStr
    is_admin : bool
    created_at : datetime
    last_login : Optional[datetime]

class ProductSchema(BaseModel):
    product_name : str
    description : str
    category : str
    price : int
    created_by : int

class CartItem(BaseModel):
    product_id: int
    price: float
    quantity: int

class OrderSchema(BaseModel):
    order_date : datetime
    status : str
    total_amount : int
    created_by : int

class OrderItemSchema(BaseModel):
    order_id : int
    product_id : int
    quantity : int

class GetProductSchema(BaseModel):
    id: int
    product_name : str
    product_image : str
    description : str
    category : str
    price : int

    class Config:
        from_attributes=True


