from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from repositories.base_repository import BaseRepository, get_db
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta
from config.database import SessionLocal
from sqlalchemy.orm import Session
from models.models import User, UserRole
from zoneinfo import ZoneInfo
from http import HTTPStatus
from jwt import encode, decode

import bcrypt
import os

security = HTTPBearer()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class SecurityRepository:
    def __init__(self, base_repository: BaseRepository = Depends()):
        self.base_repository = base_repository

    @property
    def _entity(self):
        return User

    def get_db():
        db: Session = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_access_token(self, data):
        to_encode = data.dict().copy() if hasattr(data, 'dict') else data.copy()
        expire = datetime.now(tz=ZoneInfo('UTC')) + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({'exp': expire})
        encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_user(self, data):
        user = self.base_repository.db.query(self._entity).filter(
            self._entity.email == data.email
        ).first()
        if not user:
            return None
        password_attempt = data.password.encode('utf-8')
        stored_hash = user.password.encode('utf-8')
        if bcrypt.checkpw(password_attempt, stored_hash):
            return user
        return None

    def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
        try:
            payload = decode(token.credentials, SECRET_KEY,
                             algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            role_str: str = payload.get("role")
            
            # Converter a role string do token de volta para o enum
            role = None
            for user_role in UserRole:
                if user_role.value == role_str:
                    role = user_role
                    break
            
            if not role:
                raise Exception()
            
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise Exception()
            
            return {"user": user, "user_id": user.id, "role": role}
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Acesso não autorizado.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def require_admin(current_user: dict):
        """Verifica se o usuário atual é admin ou superAdmin, caso contrário lança exceção"""
        role = current_user.get("role")
        if role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Seu usuário não tem permissão para realizar a ação.'
            )

    @staticmethod
    def require_admin_or_self(current_user: dict, target_user_id: int):
        """Verifica se o usuário atual é admin/superAdmin ou se está tentando acessar seus próprios dados"""
        role = current_user.get("role")
        is_admin = role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        if not is_admin and current_user["user_id"] != target_user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Seu usuário não tem permissão para realizar a ação.'
            )

    @staticmethod
    def prevent_admin_self_deletion(current_user: dict, target_user_id: int):
        """Impede que administradores/superAdmins se deletem a si mesmos"""
        role = current_user.get("role")
        is_admin = role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        if is_admin and current_user["user_id"] == target_user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Administradores não podem deletar a si mesmos.'
            )

    @staticmethod
    def prevent_admin_deleting_admin(user_to_delete: User):
        """Impede que administradores deletem outros administradores ou superAdmins"""
        if user_to_delete.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Administradores não podem deletar outros administradores ou superAdmins.'
            )
