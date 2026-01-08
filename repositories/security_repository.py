from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from repositories.base_repository import BaseRepository, get_db
from fastapi import Depends, HTTPException, Request
from datetime import datetime, timedelta
from config.database import SessionLocal
from sqlalchemy.orm import Session
from models.models import User, UserRole, AccessLog, AccessLogType
from zoneinfo import ZoneInfo
from http import HTTPStatus
from jwt import encode, decode
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

import bcrypt
import os

security = HTTPBearer()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 1 dia = 24 horas * 60 minutos
# Fuso horário local: UTC-3
LOCAL_TIMEZONE = ZoneInfo('America/Sao_Paulo')  # UTC-3
UTC_TIMEZONE = ZoneInfo('UTC')


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
        # Tokens JWT devem usar UTC (padrão)
        expire = datetime.now(tz=UTC_TIMEZONE) + \
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

    @staticmethod
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
        except ExpiredSignatureError as e:
            # Token expirado - criar log de logout por expiração
            try:
                # Tentar decodificar sem verificação de expiração para pegar o email
                payload = decode(token.credentials, SECRET_KEY,
                               algorithms=[ALGORITHM], options={"verify_exp": False})
                email: str = payload.get("sub")
                user = db.query(User).filter(User.email == email).first()
                if user:
                    # Criar log de logout por expiração (sem request, pois não está disponível aqui)
                    SecurityRepository.create_access_log(
                        db=db,
                        user_id=user.id,
                        log_type=AccessLogType.LOGOUT_EXPIRATION,
                        request=None
                    )
            except Exception as log_error:
                # Se não conseguir criar o log, apenas registra mas continua com o erro original
                import logging
                logging.warning(f"Erro ao criar log de logout por expiração: {log_error}")
            
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Token expirado. Faça login novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (InvalidTokenError, Exception) as e:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Acesso não autorizado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def create_access_log(db: Session, user_id: int, log_type: AccessLogType, request: Request = None):
        """Cria um log de acesso (login/logout)"""
        ip_address = None
        user_agent = None
        
        if request:
            # Obter IP do cliente
            if request.client:
                ip_address = request.client.host
            # Obter User-Agent
            user_agent = request.headers.get("user-agent")
            if user_agent and len(user_agent) > 500:
                user_agent = user_agent[:500]  # Limitar tamanho
        
        access_log = AccessLog(
            user_id=user_id,
            log_type=log_type.value,
            logged_at=datetime.now(tz=LOCAL_TIMEZONE),  # UTC-3 (America/Sao_Paulo)
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(access_log)
        db.commit()
        return access_log

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
