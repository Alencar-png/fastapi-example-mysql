from repositories.security_repository import SecurityRepository
from schemas.security_schemas import Token, SecuritySchema
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Request
from models.models import AccessLogType
from repositories.base_repository import get_db
from sqlalchemy.orm import Session

security = APIRouter()


@security.post('/login/', response_model=Token)
def login(data: SecuritySchema, request: Request, repo: SecurityRepository = Depends()):
    user = repo.verify_user(data)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Email ou Senha incorretos.'
        )
    
    access_token = repo.create_access_token(data={
        'sub': user.email,
        'role': user.role.value
    })
    
    # Criar log de login usando o mesmo banco do repositório
    SecurityRepository.create_access_log(
        db=repo.base_repository.db,
        user_id=user.id,
        log_type=AccessLogType.LOGIN,
        request=request
    )
    
    return {'access_token': access_token, 'token_type': 'Bearer'}


@security.post('/logout/')
def logout(request: Request, current_user: dict = Depends(SecurityRepository.get_current_user), db: Session = Depends(get_db)):
    """Endpoint para logout manual"""
    SecurityRepository.create_access_log(
        db=db,
        user_id=current_user["user_id"],
        log_type=AccessLogType.LOGOUT,
        request=request
    )
    
    return {"message": "Logout realizado com sucesso."}
