from repositories.base_repository import BaseRepository, CRUDBase
from schemas.user_schemas import UserCreate, UserUpdate
from fastapi import Depends, HTTPException
from models.models import User
import bcrypt


class UsersRepository(CRUDBase):
    def __init__(self, base_repository: BaseRepository = Depends()):
        self.base_repository = base_repository

    @property
    def _entity(self):
        return User

    def create(self, user_data: UserCreate):
        if self.email_exists(user_data.email):
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        # Gerar hash da senha
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=password_hash,
            is_admin=user_data.is_admin if user_data.is_admin is not None else False  
        )

        try:
            return self.base_repository.create(new_user)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Erro ao criar usuário."
            ) from e

    def find_one(self, user_id: int):
        user = self.base_repository.find_one(self._entity, user_id)
        if not user:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado.")
        return user

    def find_all(self):
        return self.base_repository.find_all(self._entity)

    def update(self, user_id: int, user_data: UserUpdate):
        try:
            user = self.base_repository.find_one(self._entity, user_id)

            if not user:
                raise HTTPException(
                    status_code=400, detail="Usuário não encontrado.")

            if user_data.email and self.email_exists(user_data.email, user_id):
                raise HTTPException(
                    status_code=400, detail="Email já está em uso.")

            self.base_repository.update_one(self._entity, user_id, user, user_data)
            return {"message": "Usuário atualizado com sucesso."}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Erro ao atualizar usuário."
            ) from e

    def delete(self, user_id):
        try:
            self.base_repository.delete_one(self._entity, user_id)
            return {"message": "Usuário removido com sucesso."}
        except Exception:
            raise HTTPException(
                status_code=500, detail="Erro ao remover Usuário.")

    def email_exists(self, email: str, id: int = 0) -> bool:
        return self.base_repository.db.query(self._entity).filter(
            self._entity.email == email,
            self._entity.id != id
        ).first() is not None
