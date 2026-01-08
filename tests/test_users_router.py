import pytest
from fastapi.testclient import TestClient
from models.models import UserRole


class TestUsersRouter:
    """Testes para as rotas de usuários"""
    
    def test_create_user_unauthorized(self, client):
        """Testa criação de usuário sem autenticação"""
        response = client.post(
            "/api/users/",
            json={
                "name": "New User",
                "email": "new@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 403
    
    def test_create_user_as_basic_user(self, client, user_token):
        """Testa criação de usuário como usuário básico (deve falhar)"""
        response = client.post(
            "/api/users/",
            json={
                "name": "New User",
                "email": "new@example.com",
                "password": "password123"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_create_user_as_admin(self, client, admin_token, db_session):
        """Testa criação de usuário como admin"""
        response = client.post(
            "/api/users/",
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "password123",
                "role": "basicUser"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New User"
        assert data["email"] == "newuser@example.com"
    
    def test_create_user_as_super_admin(self, client, super_admin_token, db_session):
        """Testa criação de usuário como superAdmin"""
        response = client.post(
            "/api/users/",
            json={
                "name": "Super New User",
                "email": "supernew@example.com",
                "password": "password123",
                "role": "admin"
            },
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Super New User"
    
    def test_list_users_unauthorized(self, client):
        """Testa listagem de usuários sem autenticação"""
        response = client.get("/api/users/")
        assert response.status_code == 403
    
    def test_list_users_as_basic_user(self, client, user_token):
        """Testa listagem de usuários como usuário básico (deve falhar)"""
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_list_users_as_admin(self, client, admin_token, test_user, test_admin_user):
        """Testa listagem de usuários como admin"""
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        emails = [user["email"] for user in data]
        assert "test@example.com" in emails
        assert "admin@example.com" in emails
    
    def test_get_user_by_id_unauthorized(self, client, test_user):
        """Testa busca de usuário por ID sem autenticação"""
        response = client.get(f"/api/users/{test_user.id}")
        assert response.status_code == 403
    
    def test_get_user_by_id_as_self(self, client, user_token, test_user):
        """Testa busca de próprio usuário"""
        response = client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    def test_get_user_by_id_as_admin(self, client, admin_token, test_user):
        """Testa busca de usuário por ID como admin"""
        response = client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
    
    def test_get_user_by_id_as_other_user(self, client, user_token, test_admin_user):
        """Testa busca de outro usuário como usuário básico (deve falhar)"""
        response = client.get(
            f"/api/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_update_user_unauthorized(self, client, test_user):
        """Testa atualização de usuário sem autenticação"""
        response = client.put(
            f"/api/users/{test_user.id}",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 403
    
    def test_update_user_as_self(self, client, user_token, test_user):
        """Testa atualização de próprio usuário"""
        response = client.put(
            f"/api/users/{test_user.id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Usuário atualizado com sucesso."
    
    def test_update_user_as_admin(self, client, admin_token, test_user):
        """Testa atualização de usuário como admin"""
        response = client.put(
            f"/api/users/{test_user.id}",
            json={"name": "Admin Updated Name"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    def test_update_user_role(self, client, admin_token, test_user):
        """Testa atualização de role do usuário"""
        response = client.put(
            f"/api/users/{test_user.id}",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
    
    def test_delete_user_unauthorized(self, client, test_user):
        """Testa exclusão de usuário sem autenticação"""
        response = client.delete(f"/api/users/{test_user.id}")
        assert response.status_code == 403
    
    def test_delete_user_as_basic_user(self, client, user_token, test_admin_user):
        """Testa exclusão de usuário como usuário básico (deve falhar)"""
        response = client.delete(
            f"/api/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_delete_user_as_admin(self, client, admin_token, db_session):
        """Testa exclusão de usuário como admin"""
        # Cria um usuário temporário para deletar
        from models.models import User
        import bcrypt
        
        password_hash = bcrypt.hashpw("12345".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        temp_user = User(
            name="Temp User",
            email="temptodelete@example.com",
            password=password_hash,
            role=UserRole.BASIC_USER
        )
        db_session.add(temp_user)
        db_session.commit()
        db_session.refresh(temp_user)
        
        response = client.delete(
            f"/api/users/{temp_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Usuário removido com sucesso."
    
    def test_delete_admin_as_admin(self, client, admin_token, test_admin_user):
        """Testa exclusão de admin por outro admin (deve falhar)"""
        response = client.delete(
            f"/api/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 403
    
    def test_delete_self_as_admin(self, client, admin_token, test_admin_user):
        """Testa exclusão de si mesmo como admin (deve falhar)"""
        response = client.delete(
            f"/api/users/{test_admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 403

