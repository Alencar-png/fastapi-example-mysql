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
