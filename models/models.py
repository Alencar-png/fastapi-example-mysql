from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum, TypeDecorator
from sqlalchemy.orm import relationship, deferred
from config.database import Base
import enum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "superAdmin"
    ADMIN = "admin"
    BASIC_USER = "basicUser"

class UserRoleType(TypeDecorator):
    """Type decorator para mapear corretamente os valores do enum UserRole"""
    impl = String
    cache_ok = True
    
    def __init__(self, length=20):
        super().__init__(length=length)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, UserRole):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        # Mapear o valor do banco para o enum
        for role in UserRole:
            if role.value == value:
                return role
        return value

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, nullable=False)
    password = deferred(Column(String(255), nullable=False))
    role = Column(UserRoleType(), nullable=False, default=UserRole.BASIC_USER)

