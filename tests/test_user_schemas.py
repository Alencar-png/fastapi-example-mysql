import pytest
from pydantic import ValidationError
from schemas.user_schemas import UserCreate, UserUpdate
from models.models import UserRole


class TestUserCreate:
    """Testes para o schema UserCreate"""
    
    def test_user_create_valid_data(self):
        """Testa criação com dados válidos"""
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="password123"
        )
        
        assert user_data.name == "Test User"
        assert user_data.email == "test@example.com"
        assert user_data.password == "password123"
        assert user_data.role == UserRole.BASIC_USER  # Valor padrão
    
    def test_user_create_with_role(self):
        """Testa criação com role específica"""
        user_data = UserCreate(
            name="Admin User",
            email="admin@example.com",
            password="password123",
            role=UserRole.ADMIN
        )
        
        assert user_data.role == UserRole.ADMIN
    
    def test_user_create_invalid_email(self):
        """Testa validação de email inválido"""
        with pytest.raises(ValidationError):
            UserCreate(
                name="Test User",
                email="invalid-email",
                password="password123"
            )
    
    def test_user_create_missing_required_fields(self):
        """Testa validação de campos obrigatórios"""
        with pytest.raises(ValidationError):
            UserCreate(
                name="Test User"
                # Faltando email e password
            )
    
    def test_user_create_with_all_roles(self):
        """Testa criação com todas as roles disponíveis"""
        roles = [UserRole.BASIC_USER, UserRole.ADMIN, UserRole.SUPER_ADMIN]
        
        for role in roles:
            user_data = UserCreate(
                name=f"User {role.value}",
                email=f"{role.value}@example.com",
                password="password123",
                role=role
            )
            assert user_data.role == role


class TestUserUpdate:
    """Testes para o schema UserUpdate"""
    
    def test_user_update_all_fields_optional(self):
        """Testa que todos os campos são opcionais"""
        user_data = UserUpdate()
        
        assert user_data.name is None
        assert user_data.email is None
        assert user_data.role is None
    
    def test_user_update_partial(self):
        """Testa atualização parcial"""
        user_data = UserUpdate(name="Updated Name")
        
        assert user_data.name == "Updated Name"
        assert user_data.email is None
        assert user_data.role is None
    
    def test_user_update_email(self):
        """Testa atualização de email"""
        user_data = UserUpdate(email="newemail@example.com")
        
        assert user_data.email == "newemail@example.com"
    
    def test_user_update_role(self):
        """Testa atualização de role"""
        user_data = UserUpdate(role=UserRole.ADMIN)
        
        assert user_data.role == UserRole.ADMIN
    
    def test_user_update_invalid_email(self):
        """Testa validação de email inválido no update"""
        with pytest.raises(ValidationError):
            UserUpdate(email="invalid-email")
    
    def test_user_update_all_fields(self):
        """Testa atualização de todos os campos"""
        user_data = UserUpdate(
            name="Updated Name",
            email="updated@example.com",
            role=UserRole.SUPER_ADMIN
        )
        
        assert user_data.name == "Updated Name"
        assert user_data.email == "updated@example.com"
        assert user_data.role == UserRole.SUPER_ADMIN

