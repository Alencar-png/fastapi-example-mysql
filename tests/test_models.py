import pytest
from models.models import User, UserRole, UserRoleType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class TestUserRole:
    """Testes para o enum UserRole"""
    
    def test_user_role_values(self):
        """Testa se os valores do enum estão corretos"""
        assert UserRole.SUPER_ADMIN.value == "superAdmin"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.BASIC_USER.value == "basicUser"
    
    def test_user_role_enum_membership(self):
        """Testa se os valores são membros do enum"""
        assert UserRole.SUPER_ADMIN in UserRole
        assert UserRole.ADMIN in UserRole
        assert UserRole.BASIC_USER in UserRole


class TestUserRoleType:
    """Testes para o TypeDecorator UserRoleType"""
    
    def test_process_bind_param_with_enum(self):
        """Testa se process_bind_param converte enum para string"""
        role_type = UserRoleType()
        result = role_type.process_bind_param(UserRole.SUPER_ADMIN, None)
        assert result == "superAdmin"
    
    def test_process_bind_param_with_string(self):
        """Testa se process_bind_param retorna string diretamente"""
        role_type = UserRoleType()
        result = role_type.process_bind_param("admin", None)
        assert result == "admin"
    
    def test_process_bind_param_with_none(self):
        """Testa se process_bind_param retorna None quando recebe None"""
        role_type = UserRoleType()
        result = role_type.process_bind_param(None, None)
        assert result is None
    
    def test_process_result_value_with_valid_role(self):
        """Testa se process_result_value converte string para enum"""
        role_type = UserRoleType()
        result = role_type.process_result_value("superAdmin", None)
        assert result == UserRole.SUPER_ADMIN
    
    def test_process_result_value_with_none(self):
        """Testa se process_result_value retorna None quando recebe None"""
        role_type = UserRoleType()
        result = role_type.process_result_value(None, None)
        assert result is None


class TestUserModel:
    """Testes para o modelo User"""
    
    def test_user_creation(self, db_session):
        """Testa a criação de um usuário"""
        user = User(
            name="Test User",
            email="test@example.com",
            password="hashed_password",
            role=UserRole.BASIC_USER
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password == "hashed_password"
        assert user.role == UserRole.BASIC_USER
    
    def test_user_default_role(self, db_session):
        """Testa se o role padrão é BASIC_USER"""
        user = User(
            name="Test User",
            email="test2@example.com",
            password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.role == UserRole.BASIC_USER
    
    def test_user_with_different_roles(self, db_session):
        """Testa criação de usuários com diferentes roles"""
        roles = [UserRole.BASIC_USER, UserRole.ADMIN, UserRole.SUPER_ADMIN]
        
        for i, role in enumerate(roles):
            user = User(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password="hashed_password",
                role=role
            )
            db_session.add(user)
        
        db_session.commit()
        
        users = db_session.query(User).all()
        assert len(users) == 3
        assert users[0].role == UserRole.BASIC_USER
        assert users[1].role == UserRole.ADMIN
        assert users[2].role == UserRole.SUPER_ADMIN
    
    def test_user_email_unique(self, db_session):
        """Testa se o email deve ser único"""
        user1 = User(
            name="User 1",
            email="same@example.com",
            password="hashed_password"
        )
        user2 = User(
            name="User 2",
            email="same@example.com",
            password="hashed_password"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # SQLAlchemy vai levantar exceção
            db_session.commit()
        
        db_session.rollback()

