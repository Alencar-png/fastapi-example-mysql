from repositories.security_repository import SecurityRepository
from schemas.security_schemas import Token, SecuritySchema
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException

security = APIRouter()


@security.post('/login/', response_model=Token)
def login(data: SecuritySchema, repo: SecurityRepository = Depends()):
    user = repo.verify_user(data)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Email ou Senha incorretos.'
        )
    access_token = repo.create_access_token(data={'sub': user.email})
    return {'access_token': access_token, 'token_type': 'Bearer'}
