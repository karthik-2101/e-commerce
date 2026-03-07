from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from app.database import Base
from datetime import datetime, timedelta
# from sqlalchemy.orm import relationship

class User1(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	first_name = Column(String)
	last_name = Column(String)
	email = Column(String, unique=True, nullable=False)
	password = Column(String, nullable=False)
	is_admin = Column(Boolean)
	created_at = Column(DateTime, nullable=False, default=datetime.now())
	last_login = Column(DateTime, nullable=True)
	session_id = Column(String, nullable=True)
	# order = relationship("Order", back_populates='user')

class Product(Base):
	__tablename__ = 'products'  
	id = Column(Integer, primary_key=True)
	product_name = Column(String) 
	description = Column(String)  
	category = Column(String)
	price = Column(Float)
	created_at = Column(DateTime, nullable=False, default=datetime.now())
	created_by = Column(Integer)
	updated_at = Column(DateTime, nullable=True)
	updated_by = Column(Integer, nullable=True)  
	delivery_in_days = Column(Integer, nullable=True)
	product_image = Column(String, nullable=True)
	is_active = Column(Boolean, default=True)
	# user = relationship("User1", back_populates='product')
	# order = relationship("Order", back_populates='product')

class Order(Base):
	__tablename__ = 'orders'                 
	id = Column(Integer, primary_key=True)
	order_date = Column(DateTime, default=datetime.now())
	status = Column(String)
	total_amount = Column(Integer)
	created_by = Column(Integer)
	# user = relationship("User1", back_populates='order')
	# product = relationship("Product", back_populates='order')

class OrderItem(Base):
	__tablename__ = 'orderitem'
	id = Column(Integer, primary_key=True)
	order_id = Column(Integer, ForeignKey("orders.id"))
	product_id = Column(Integer, ForeignKey("products.id"))
	quantity = Column(Integer)
	# order = relationship("Order", back_populates='orderitem')
	# product = relationship("Product", back_populates='orderitem')

class BlacklistedToken(Base):
	__tablename__ = 'blacklisted_tokens'
	id = Column(Integer, primary_key=True)
	jti = Column(String)
	expires_at = Column(DateTime(timezone=True), nullable=True)
