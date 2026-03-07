from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, status
from fastapi.responses import JSONResponse
from app.schema import UserCreate, UserResponse, GetProductSchema
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import User1, Product, Order, OrderItem
from app.utils import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user, clear_cart, get_user
from pydantic import EmailStr
from typing import Dict
from fastapi.exceptions import HTTPException
from datetime import datetime, timedelta
import os, shutil, uuid
# import secrets

router = APIRouter()

# @router.get('/secret')
# async def secret():
#     key = secrets.token_urlsafe(32)
#     print(key)
#     return True

CART_SESSION_KEY = "cart"  

UPLOAD_FILE = "description"
os.makedirs(UPLOAD_FILE, exist_ok=True)

DELETE_FILE = "deleted_description"
os.makedirs(DELETE_FILE, exist_ok=True)

UPLOAD_IMAGE = "images"
os.makedirs(UPLOAD_IMAGE, exist_ok=True)

DELETE_IMAGE = "deleted_images"
os.makedirs(DELETE_IMAGE, exist_ok=True)

@router.get('/')
async def welcome():
    return JSONResponse(status_code=200, content={'message':'welcome to the e-commerce application'})

@router.post('/createuser', response_model=UserResponse)
async def add_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        print("Hii-->>>")
        hashed_password = hash_password(user.password)
        print("firstname->>>",user.first_name)
        db_user1 = User1(first_name=user.first_name, last_name=user.last_name, email=user.email, password=hashed_password, is_admin=user.is_admin)
        print("DB User-->>>", db_user1)
        db.add(db_user1)
        db.commit()
        db.refresh(db_user1)
    except Exception as e:
        print(e)
        db.close()
    return JSONResponse(status_code=201, content={'message':'User Created'})

@router.post('/loginuser')
async def login(  
    email: EmailStr = Form(), 
    password: str = Form(),
    db: Session = Depends(get_db)
):
    user = get_user(db, email)
    session_id = str(uuid.uuid4())
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if not verify_password(password, user.password): 
        raise HTTPException(status_code=404, detail='Authentication failed')
    user.session_id = session_id
    db.commit()
    return {
        "access_token":create_access_token(email, session_id),
        "refresh_token":create_refresh_token(email, session_id)
    }

@router.get('/currentuser')
async def current_user(current_user_id: int = Depends(get_current_user)):
    return JSONResponse(status_code=200, content={'message':'Successfully authenticated', 'user_id':current_user_id})

@router.post("/logout")
async def logout(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.get(User1, current_user_id)
    user.session_id = "NULL"
    db.commit()
    return JSONResponse(status_code=200, content={'message':'logged out successfully'})

@router.post('/addproduct')
async def add_product(
    current_user_id: int = Depends(get_current_user),
    product_name: str = Form(),
    price: float = Form(),
    category: str = Form(),
    description: UploadFile = File(),
    image: UploadFile = File(),
    db: Session = Depends(get_db)
):
    try:
        user = db.get(User1, current_user_id)
        if user.is_admin:
            db_product = Product(product_name=product_name, price=price, category=category, created_by=current_user_id, 
                                 description=description.filename, product_image=image.filename, delivery_in_days=7)
            db.add(db_product)
            db.commit()
            db.refresh(db_product)
            unique_filename = f"{db_product.id}_{description.filename}"
            file_location = os.path.join(UPLOAD_FILE, unique_filename)
            with open(file_location, "wb") as f:
                f.write(await description.read())
        else:
            return JSONResponse(status_code=401, content={'detail':'You are not authorized to add product'})
    except Exception as e:
        print(e)
        db.close()
    return JSONResponse(status_code=201, content={'message':'Product added'})

@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    # current_user: int = Depends(get_current_user),
    product_id: str = Form(),
    quantity: int = Form(),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    cart: Dict[str, Dict] = request.session.get(CART_SESSION_KEY, {})

    if product_id not in cart:
        cart[product_id] = {"quantity": 0, "price": product.price}
    cart[product_id]["quantity"] += quantity

    request.session[CART_SESSION_KEY] = cart
    return JSONResponse(status_code=200, content={"message": "Item added to cart", "cart": cart[product_id]})

@router.post("/cart/remove/{product_id}")
async def remove_from_cart(request: Request, product_id: str):
    cart = request.session.get("cart", {})
    if product_id in cart:
        del cart[product_id] 
        request.session[CART_SESSION_KEY] = cart
        return JSONResponse(status_code=200, content={"message": f"Removed product {product_id} from cart."})
    return JSONResponse(status_code=200, content={"message": "Item not found in cart."})

@router.post('/makeorder')
async def make_order(
    request: Request,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = request.session.get("cart", {})
    if len(cart)==0: 
        return JSONResponse(status_code=404, content={"detail":"No items in cart to make order"})
    try:
        order = Order(created_by = current_user_id, total_amount = 0, status='PENDING')
        db.add(order)
        db.commit()
        db.refresh(order)

        total_amount = 0
        order_items_list = []

        for product_id_str, item_data in cart.items():
            product_id = int(product_id_str)
            quantity = item_data["quantity"]
            price = item_data["price"]

            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

            total_price = price * quantity
            total_amount += total_price

            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
            )
            order_items_list.append(order_item)

        db.add_all(order_items_list)
        order.total_amount = total_amount
        db.commit()
        db.refresh(order)
        clear_cart(request)
    except Exception as e:
        print("exception-->>", e)
    finally:
        db.close()
    return JSONResponse(status_code=201, content={"message": "Order created successfully", "order": order})

@router.get("/viewcart")
async def view_cart(request: Request):#, current_user_id: int = Depends(get_current_user)):
    cart = request.session.get("cart", {})
    return JSONResponse(status_code=200, content={'cart':cart})

@router.patch("/updateproduct/{id}")
async def update_product(
    id: int,
    current_user_id: int = Depends(get_current_user),
    product_name : str = Form(),
    description : UploadFile = File(),
    category : str = Form(),
    price : int = Form(),
    image : UploadFile = File(),
    db: Session = Depends(get_db)
):
    try:
        user = db.get(User1, current_user_id)
        if user.is_admin:
            product = db.get(Product, id)

            product.product_name = product_name
            product.description = description.filename
            product.category = category
            product.price = price
            product.updated_by = user.id
            product.updated_at = datetime.now()
            product.product_image = image.filename

            db.commit()

            unique_filename = f"{product.id}_{description.filename}"
            description_location = os.path.join(UPLOAD_FILE, unique_filename)
            with open(description_location, "wb") as f:
                f.write(await description.read())

            unique_image = f"{product.id}_{image.filename}"
            image_location = os.path.join(UPLOAD_IMAGE, unique_image)
            with open(image_location, "wb") as f:
                f.write(await image.read())
        else:
            return JSONResponse(status_code=401, content={'detail':'You are not authorized to update product'})
    except Exception as e:
        print(e)
    finally:
        db.close()
    return JSONResponse(status_code=200, content={'message':'Product updated successfully'})

@router.get("/getallproducts")
async def get_product(
    db: Session = Depends(get_db)
):
    products = db.query(Product).all()
    return [GetProductSchema.from_orm(product) for product in products]

@router.get("/getproduct/{id}")
async def get_product(
    id: int,
    # current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.get(Product, id)
    description_name = f"{product.id}_{product.description}"
    description_location = os.path.join(UPLOAD_FILE, description_name)
    with open(description_location, "r") as f:
        description_text = f.read() 

    image_name = f"{product.id}_{product.product_image}"
    image_path = os.path.join(os.getcwd(), UPLOAD_IMAGE, image_name)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="File Not Found")
        
    content = {
        'product_id' : product.id,
        'product_name' : product.product_name,
        'product_image' : image_path,
        'description' : description_text,
        'price': product.price,
        'Expected delivery date': str(datetime.now().date()+timedelta(days=7))
    }
    return JSONResponse(status_code=200, content=content)

@router.delete("/deleteproduct/{id}")
async def delete_product(
    id: int,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = db.get(User1, current_user_id)
        if user.is_admin:
            product = db.get(Product, id)
            source_file = os.path.join(os.getcwd(), UPLOAD_FILE, f"{product.id}_{product.description}")
            source_image = os.path.join(os.getcwd(), UPLOAD_IMAGE, f"{product.id}_{product.product_image}")

            destination_file = os.path.join(os.getcwd(), DELETE_FILE, f"{product.id}_{product.description}")
            destination_image = os.path.join(os.getcwd(), DELETE_IMAGE, f"{product.id}_{product.product_image}")

            if product.is_active == True:
                product.is_active = False
                shutil.move(source_file, destination_file)
                shutil.move(source_image, destination_image)
                db.commit()
            else:
                return JSONResponse(status_code=200, content={'message':'Product already removed'})
        else:
            raise HTTPException(status_code=401, detail="You are not authorized to delete product")
    except Exception as e:
        print(e)
    finally:
        db.close()
    return JSONResponse(status_code=200, content={'message':'Product removed'})

@router.delete("/retrieveproduct/{id}")
async def retrieve_product(
    id: int,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = db.get(User1, current_user_id)
        if user.is_admin:
            product = db.get(Product, id)
            source_file = os.path.join(os.getcwd(), UPLOAD_FILE, f"{product.id}_{product.description}")
            source_image = os.path.join(os.getcwd(), UPLOAD_IMAGE, f"{product.id}_{product.product_image}")

            destination_file = os.path.join(os.getcwd(), DELETE_FILE, f"{product.id}_{product.description}")
            destination_image = os.path.join(os.getcwd(), DELETE_IMAGE, f"{product.id}_{product.product_image}")

            if product.is_active == False:
                product.is_active = True
                shutil.move(destination_file, source_file)
                shutil.move(destination_image, source_image)
                db.commit()
            else:
                return JSONResponse(status_code=200, content={'message':'Product already in products list'})
        else:
            raise HTTPException(status_code=401, detail="You are not authorized to update product")
    except Exception as e:
        print(e)
    finally:
        db.close()
    return JSONResponse(status_code=200, content={'message':'Product updated'})