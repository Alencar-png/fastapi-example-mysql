from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from repositories.base_repository import BaseRepository
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta
from config.database import SessionLocal
from sqlalchemy.orm import Session
from models.models import User
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
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise Exception()
            return {"user": user, "user_id": user.id, "is_admin": user.is_admin}
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Acesso não autorizado.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def require_admin(current_user: dict):
        """Verifica se o usuário atual é admin, caso contrário lança exceção"""
        if not current_user["is_admin"]:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Seu usuário não tem permissão para realizar a ação.'
            )

    @staticmethod
    def require_admin_or_self(current_user: dict, target_user_id: int):
        """Verifica se o usuário atual é admin ou se está tentando acessar seus próprios dados"""
        if not current_user["is_admin"] and current_user["user_id"] != target_user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Seu usuário não tem permissão para realizar a ação.'
            )

    @staticmethod
    def prevent_admin_self_deletion(current_user: dict, target_user_id: int):
        """Impede que administradores se deletem a si mesmos"""
        if current_user["is_admin"] and current_user["user_id"] == target_user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Administradores não podem deletar a si mesmos.'
            )

    @staticmethod
    def prevent_admin_deleting_admin(user_to_delete: User):
        """Impede que administradores deletem outros administradores"""
        if user_to_delete.is_admin:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, 
                detail='Administradores não podem deletar outros administradores.'
            )
