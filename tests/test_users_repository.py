import pytest
from fastapi import HTTPException
from repositories.users_repository import UsersRepository
from schemas.user_schemas import UserCreate, UserUpdate
from models.models import User, UserRole
import bcrypt


class TestUsersRepository:
    """Testes para UsersRepository"""
    
    def test_create_user_success(self, users_repository):
        """Testa criação de usuário com sucesso"""
        user_data = UserCreate(
            name="New User",
            email="newuser@example.com",
            password="password123",
            role=UserRole.BASIC_USER
        )
        
        user = users_repository.create(user_data)
        
        assert user.id is not None
        assert user.name == "New User"
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.BASIC_USER
        # Verifica se a senha foi hasheada
        assert user.password != "password123"
        assert bcrypt.checkpw("password123".encode('utf-8'), user.password.encode('utf-8'))
    
    def test_create_user_duplicate_email(self, users_repository, test_user):
        """Testa criação de usuário com email duplicado"""
        user_data = UserCreate(
            name="Another User",
            email="test@example.com",  # Email já existe
            password="password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            users_repository.create(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email já cadastrado" in exc_info.value.detail
    
    def test_create_user_default_role(self, users_repository):
        """Testa criação de usuário sem especificar role"""
        user_data = UserCreate(
            name="Default Role User",
            email="default@example.com",
            password="password123"
        )
        
        user = users_repository.create(user_data)
        assert user.role == UserRole.BASIC_USER
    
    def test_find_one_success(self, users_repository, test_user):
        """Testa busca de usuário por ID"""
        user = users_repository.find_one(test_user.id)
        
        assert user.id == test_user.id
        assert user.name == test_user.name
        assert user.email == test_user.email
    
    def test_find_one_not_found(self, users_repository):
        """Testa busca de usuário inexistente"""
        with pytest.raises(HTTPException) as exc_info:
            users_repository.find_one(999)
        
        assert exc_info.value.status_code == 404
        assert "Usuário não encontrado" in exc_info.value.detail
    
    def test_find_all(self, users_repository, test_user, test_admin_user):
        """Testa busca de todos os usuários"""
        users = users_repository.find_all()
        
        assert len(users) >= 2
        user_ids = [u.id for u in users]
        assert test_user.id in user_ids
        assert test_admin_user.id in user_ids
    
    def test_update_user_success(self, users_repository, test_user):
        """Testa atualização de usuário com sucesso"""
        user_data = UserUpdate(
            name="Updated Name",
            email="updated@example.com"
        )
        
        result = users_repository.update(test_user.id, user_data)
        
        assert result["message"] == "Usuário atualizado com sucesso."
        
        # Verifica se foi atualizado
        updated_user = users_repository.find_one(test_user.id)
        assert updated_user.name == "Updated Name"
        assert updated_user.email == "updated@example.com"
    
    def test_update_user_role(self, users_repository, test_user):
        """Testa atualização de role do usuário"""
        user_data = UserUpdate(role=UserRole.ADMIN)
        
        users_repository.update(test_user.id, user_data)
        
        updated_user = users_repository.find_one(test_user.id)
        assert updated_user.role == UserRole.ADMIN
    
    def test_update_user_not_found(self, users_repository):
        """Testa atualização de usuário inexistente"""
        user_data = UserUpdate(name="Updated Name")
        
        with pytest.raises(HTTPException) as exc_info:
            users_repository.update(999, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Usuário não encontrado" in exc_info.value.detail
    
    def test_update_user_duplicate_email(self, users_repository, test_user, test_admin_user):
        """Testa atualização com email duplicado"""
        user_data = UserUpdate(email=test_admin_user.email)
        
        with pytest.raises(HTTPException) as exc_info:
            users_repository.update(test_user.id, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email já está em uso" in exc_info.value.detail
    
    def test_update_user_same_email_allowed(self, users_repository, test_user):
        """Testa que atualizar com o mesmo email é permitido"""
        user_data = UserUpdate(email=test_user.email)
        
        result = users_repository.update(test_user.id, user_data)
        assert result["message"] == "Usuário atualizado com sucesso."
    
    def test_delete_user_success(self, users_repository, db_session):
        """Testa exclusão de usuário com sucesso"""
        # Cria um usuário temporário para deletar
        password_hash = bcrypt.hashpw("12345".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        temp_user = User(
            name="Temp User",
            email="temp@example.com",
            password=password_hash,
            role=UserRole.BASIC_USER
        )
        db_session.add(temp_user)
        db_session.commit()
        db_session.refresh(temp_user)
        
        result = users_repository.delete(temp_user.id)
        
        assert result["message"] == "Usuário removido com sucesso."
        
        # Verifica se foi deletado
        with pytest.raises(HTTPException):
            users_repository.find_one(temp_user.id)
    
    def test_email_exists_true(self, users_repository, test_user):
        """Testa verificação de email existente"""
        assert users_repository.email_exists("test@example.com") is True
    
    def test_email_exists_false(self, users_repository):
        """Testa verificação de email inexistente"""
        assert users_repository.email_exists("nonexistent@example.com") is False
    
    def test_email_exists_excluding_current_user(self, users_repository, test_user):
        """Testa verificação de email excluindo o próprio usuário"""
        # O email existe, mas é do próprio usuário
        assert users_repository.email_exists("test@example.com", test_user.id) is False

