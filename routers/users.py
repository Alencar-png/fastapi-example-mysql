from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus
from repositories.users_repository import UsersRepository
from repositories.security_repository import SecurityRepository
from schemas.user_schemas import UserCreate, UserUpdate
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

user = APIRouter()

@user.post("/users/", status_code=201)
def create_user(user_data: UserCreate,
                repo: UsersRepository = Depends(),
                current_user : SecurityRepository.get_current_user = Depends()):
    SecurityRepository.require_admin(current_user)
    return repo.create(user_data)

@user.get("/users/")
def read_users(repo: UsersRepository = Depends(),
               current_user : SecurityRepository.get_current_user = Depends()):
    SecurityRepository.require_admin(current_user)
    return repo.base_repository.db.query(repo._entity).all()

@user.get("/users/{user_id}")
def read_user(user_id: int, repo: UsersRepository = Depends(),
              current_user : SecurityRepository.get_current_user = Depends()):
    SecurityRepository.require_admin_or_self(current_user, user_id)
    return repo.find_one(user_id)

@user.put("/users/{user_id}",)
def update_user(user_id: int, 
                user_data: UserUpdate, 
                current_user : SecurityRepository.get_current_user = Depends(),
                repo: UsersRepository = Depends()):
    
    SecurityRepository.require_admin_or_self(current_user, user_id)
    return repo.update(user_id, user_data)


@user.delete("/users/{user_id}")
def delete_user(user_id: int,
                current_user: SecurityRepository.get_current_user = Depends(),
                repo: UsersRepository = Depends()):
    SecurityRepository.require_admin(current_user)
    SecurityRepository.prevent_admin_self_deletion(current_user, user_id)
    
    user_to_delete = repo.find_one(user_id)
    SecurityRepository.prevent_admin_deleting_admin(user_to_delete)
    
    return repo.delete(user_id)
