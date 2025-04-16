from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, deferred
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, nullable=False)
    password = deferred(Column(String(255), nullable=False))
    is_admin = Column(Boolean, nullable=False)

