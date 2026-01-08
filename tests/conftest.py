import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from models.models import Base, User, UserRole
from repositories.base_repository import get_db, BaseRepository
from repositories.users_repository import UsersRepository
from repositories.security_repository import SecurityRepository
from main import app
import bcrypt
import os
from jwt import encode
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Configurar SECRET_KEY para testes
TEST_SECRET_KEY = os.getenv('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ['SECRET_KEY'] = TEST_SECRET_KEY


# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Cria uma sessão de banco de dados para cada teste"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def get_test_db():
    """Função para obter o banco de teste - será sobrescrita no fixture client"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de teste para a aplicação FastAPI com override do banco"""
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from jwt import decode
    from fastapi import HTTPException, Depends
    from http import HTTPStatus
    from repositories.security_repository import security as security_bearer
    
    def override_get_db():
        yield db_session
    
    def override_get_current_user(
        token: HTTPAuthorizationCredentials = Depends(security_bearer)
    ):
        """Override do get_current_user para usar o banco de teste"""
        ALGORITHM = 'HS256'
        
        try:
            payload = decode(token.credentials, TEST_SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            role_str: str = payload.get("role")
            
            # Converter a role string do token de volta para o enum
            role = None
            for user_role in UserRole:
                if user_role.value == role_str:
                    role = user_role
                    break
            
            if not role:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="Acesso não autorizado.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user = db_session.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="Acesso não autorizado.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return {"user": user, "user_id": user.id, "role": role}
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Acesso não autorizado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    app.dependency_overrides[get_db] = override_get_db
    # Override do get_current_user usando a referência exata
    app.dependency_overrides[SecurityRepository.get_current_user] = override_get_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def base_repository(db_session):
    """Fixture para BaseRepository"""
    return BaseRepository(db=db_session)


@pytest.fixture
def users_repository(base_repository):
    """Fixture para UsersRepository"""
    return UsersRepository(base_repository=base_repository)


@pytest.fixture
def security_repository(base_repository):
    """Fixture para SecurityRepository"""
    return SecurityRepository(base_repository=base_repository)


@pytest.fixture
def test_user(db_session):
    """Cria um usuário de teste"""
    password_hash = bcrypt.hashpw("12345".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        name="Test User",
        email="test@example.com",
        password=password_hash,
        role=UserRole.BASIC_USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session):
    """Cria um usuário admin de teste"""
    password_hash = bcrypt.hashpw("12345".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        name="Admin User",
        email="admin@example.com",
        password=password_hash,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_super_admin_user(db_session):
    """Cria um usuário superAdmin de teste"""
    password_hash = bcrypt.hashpw("12345".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        name="Super Admin User",
        email="superadmin@example.com",
        password=password_hash,
        role=UserRole.SUPER_ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user




# TEST_SECRET_KEY já definido no topo do arquivo

def create_test_token(email: str, role: UserRole):
    """Helper para criar tokens JWT para testes"""
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    to_encode = {'sub': email, 'role': role.value}
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encoded_jwt = encode(to_encode, TEST_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@pytest.fixture
def admin_token(test_admin_user):
    """Gera um token JWT para o usuário admin"""
    return create_test_token(test_admin_user.email, test_admin_user.role)


@pytest.fixture
def super_admin_token(test_super_admin_user):
    """Gera um token JWT para o usuário superAdmin"""
    return create_test_token(test_super_admin_user.email, test_super_admin_user.role)


@pytest.fixture
def user_token(test_user):
    """Gera um token JWT para o usuário básico"""
    return create_test_token(test_user.email, test_user.role)

