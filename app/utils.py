from fastapi import Depends, Request
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import jwt, JWTError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import User1
from fastapi.exceptions import HTTPException
from pydantic import EmailStr

ACCESS_TOKEN_EXPIRE_MINUTES = 30  
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 
ALGORITHM = "HS256"
JWT_SECRET_KEY = 'iZkeXGHw91i4cQHdGq1N_jmGufpY0pJ_Ps5fXxqReVA'    
JWT_REFRESH_SECRET_KEY = 'rQMJz5CUeutfpQRzJ0j21HBQiXabxmAqeWVxOqnZRcA'

bearer = HTTPBearer()

password_hash = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, email: EmailStr):
    user = db.query(User1).filter(User1.email == email).first()
    return user

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(subject: str, session_id: str, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), "session_id": str(session_id)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str, session_id: str, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), "session_id": str(session_id)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt

def get_current_user(
    credential: HTTPAuthorizationCredentials = Depends(bearer), 
    db: Session = Depends(get_db)
):
    try:
        token = credential.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])

        session_id = payload.get("session_id")
        if not session_id:
            raise HTTPException(status_code=404, detail='Invalid token..')

        session_user = db.query(User1).filter(User1.session_id == session_id).first()
        if not session_user:
            raise HTTPException(status_code=404, detail='Invalid Session Id')
        
        email : str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=404, detail='User not found')
        
        user = db.query(User1).filter(User1.email == email).first()
        return user.id
    except JWTError as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid token")
    
def clear_cart(request: Request):
    request.session["cart"] = {}  

# jti = payload.get("jti")
# if not jti:
#     raise HTTPException(status_code=404, detail='Invalid token')

# blacklisted_token = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()

# if blacklisted_token:
#     raise HTTPException(status_code=400, detail='Token has been blacklisted')

# async def log_out(
#     credential: HTTPAuthorizationCredentials = Depends(bearer), 
#     db: Session = Depends(get_db)
# ):
#     try:
#         token = credential.credentials
#         payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
#         jti = payload.get("jti")
#         exp = payload.get("exp")

#         if not jti or not exp:
#             raise HTTPException(status_code=400, detail="Invalid token payload")

#         blacklisted_token = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()

#         if blacklisted_token:
#             raise HTTPException(status_code=400, detail='User already logged out')

#         expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

#         blacklisted_token = BlacklistedToken(jti=jti, expires_at=expires_at)
#         db.add(blacklisted_token)
#         db.commit()
#         return "Successfully logged out"
#     except JWTError as e:
#         print(e)
#         raise HTTPException(status_code=401, detail="Invalid token")