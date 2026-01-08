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
    
    def test_login_creates_access_log(self, client, test_user, db_session):
        """Testa que um log de login é criado quando o usuário faz login"""
        from models.models import AccessLog, AccessLogType
        
        # Contar logs antes do login
        logs_before = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGIN.value
        ).count()
        
        # Fazer login
        response = client.post(
            "/api/login/",
            json={
                "email": test_user.email,
                "password": "12345"
            }
        )
        
        assert response.status_code == 200
        
        # Verificar que um log foi criado
        logs_after = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGIN.value
        ).count()
        
        assert logs_after == logs_before + 1
        
        # Verificar detalhes do log criado
        log = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGIN.value
        ).order_by(AccessLog.logged_at.desc()).first()
        
        assert log is not None
        assert log.user_id == test_user.id
        assert log.log_type == AccessLogType.LOGIN.value
    
    def test_logout_creates_access_log(self, client, test_user, user_token, db_session):
        """Testa que um log de logout é criado quando o usuário faz logout"""
        from models.models import AccessLog, AccessLogType
        
        # Contar logs antes do logout
        logs_before = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGOUT.value
        ).count()
        
        # Fazer logout
        response = client.post(
            "/api/logout/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Logout realizado com sucesso."
        
        # Verificar que um log foi criado
        logs_after = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGOUT.value
        ).count()
        
        assert logs_after == logs_before + 1
        
        # Verificar detalhes do log criado
        log = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGOUT.value
        ).order_by(AccessLog.logged_at.desc()).first()
        
        assert log is not None
        assert log.user_id == test_user.id
        assert log.log_type == AccessLogType.LOGOUT.value
    
    def test_expired_token_creates_logout_expiration_log(self, client, test_user, db_session):
        """Testa que um log de logout por expiração é criado quando um token expirado é usado"""
        from models.models import AccessLog, AccessLogType
        from jwt import encode
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        from tests.conftest import TEST_SECRET_KEY
        
        # Criar um token expirado
        ALGORITHM = 'HS256'
        to_encode = {'sub': test_user.email, 'role': test_user.role.value}
        expire = datetime.now(tz=ZoneInfo('UTC')) - timedelta(days=1)  # Token expirado há 1 dia
        to_encode.update({'exp': expire})
        expired_token = encode(to_encode, TEST_SECRET_KEY, algorithm=ALGORITHM)
        
        # Contar logs antes
        logs_before = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGOUT_EXPIRATION.value
        ).count()
        
        # Tentar usar o token expirado
        response = client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401  # Não autorizado
        
        # Verificar que um log de logout por expiração foi criado
        logs_after = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGOUT_EXPIRATION.value
        ).count()
        
        assert logs_after == logs_before + 1
        
        # Verificar detalhes do log criado
        log = db_session.query(AccessLog).filter(
            AccessLog.user_id == test_user.id,
            AccessLog.log_type == AccessLogType.LOGOUT_EXPIRATION.value
        ).order_by(AccessLog.logged_at.desc()).first()
        
        assert log is not None
        assert log.user_id == test_user.id
        assert log.log_type == AccessLogType.LOGOUT_EXPIRATION.value
    
    def test_logout_requires_authentication(self, client):
        """Testa que logout requer autenticação"""
        response = client.post("/api/logout/")
        assert response.status_code == 403  # Forbidden - sem token

