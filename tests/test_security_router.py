import pytest
from fastapi.testclient import TestClient
from models.models import UserRole
from jwt import decode
from tests.conftest import TEST_SECRET_KEY

ALGORITHM = 'HS256'


class TestSecurityRouter:
    """Testes para as rotas de segurança"""
    
    def test_login_success_with_basic_user(self, client, test_user):
        """Testa login bem-sucedido com usuário básico"""
        response = client.post(
            "/api/login/",
            json={
                "email": test_user.email,
                "password": "12345"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        
        # Decodificar o token e verificar se contém a role
        token = data["access_token"]
        payload = decode(token, TEST_SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == test_user.email
        assert payload["role"] == test_user.role.value
    
    def test_login_success_with_admin_user(self, client, test_admin_user):
        """Testa login bem-sucedido com usuário admin"""
        response = client.post(
            "/api/login/",
            json={
                "email": test_admin_user.email,
                "password": "12345"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        
        # Decodificar o token e verificar se contém a role admin
        token = data["access_token"]
        payload = decode(token, TEST_SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == test_admin_user.email
        assert payload["role"] == UserRole.ADMIN.value
    
    def test_login_success_with_super_admin_user(self, client, test_super_admin_user):
        """Testa login bem-sucedido com usuário superAdmin"""
        response = client.post(
            "/api/login/",
            json={
                "email": test_super_admin_user.email,
                "password": "12345"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        
        # Decodificar o token e verificar se contém a role superAdmin
        token = data["access_token"]
        payload = decode(token, TEST_SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == test_super_admin_user.email
        assert payload["role"] == UserRole.SUPER_ADMIN.value
    
    def test_login_invalid_email(self, client):
        """Testa login com email inválido"""
        response = client.post(
            "/api/login/",
            json={
                "email": "nonexistent@example.com",
                "password": "12345"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Email ou Senha incorretos."
    
    def test_login_invalid_password(self, client, test_user):
        """Testa login com senha inválida"""
        response = client.post(
            "/api/login/",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Email ou Senha incorretos."
    
    def test_login_missing_email(self, client):
        """Testa login sem email"""
        response = client.post(
            "/api/login/",
            json={
                "password": "12345"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_missing_password(self, client, test_user):
        """Testa login sem senha"""
        response = client.post(
            "/api/login/",
            json={
                "email": test_user.email
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_empty_body(self, client):
        """Testa login com body vazio"""
        response = client.post(
            "/api/login/",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_token_can_be_used_for_authentication(self, client, test_user):
        """Testa que o token retornado pode ser usado para autenticação"""
        # Fazer login
        login_response = client.post(
            "/api/login/",
            json={
                "email": test_user.email,
                "password": "12345"
            }
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Usar o token para acessar um endpoint protegido
        response = client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

