# Testes do Módulo de Users

Este diretório contém todos os testes para o módulo de usuários da aplicação.

## Estrutura

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartilhadas
├── test_models.py           # Testes para modelos
├── test_user_schemas.py     # Testes para schemas
├── test_users_repository.py # Testes para repositórios
└── test_users_router.py     # Testes para rotas/endpoints
```

## Instalação

Instale as dependências de teste:

```bash
pip install -r requirements.txt
```

## Executando os Testes

### Executar todos os testes

```bash
pytest
```

### Executar testes específicos

```bash
# Testes de modelos
pytest tests/test_models.py

# Testes de schemas
pytest tests/test_user_schemas.py

# Testes de repositórios
pytest tests/test_users_repository.py

# Testes de rotas
pytest tests/test_users_router.py
```

### Executar com cobertura

```bash
pytest --cov=. --cov-report=html
```

### Executar com verbose

```bash
pytest -v
```

## Descrição dos Testes

### test_models.py
- Testa o enum `UserRole` e seus valores
- Testa o `UserRoleType` (TypeDecorator)
- Testa criação e validação do modelo `User`

### test_user_schemas.py
- Testa validação do schema `UserCreate`
- Testa validação do schema `UserUpdate`
- Testa valores padrão e validações de campos

### test_users_repository.py
- Testa criação de usuários
- Testa busca de usuários (find_one, find_all)
- Testa atualização de usuários
- Testa exclusão de usuários
- Testa validações de email duplicado

### test_users_router.py
- Testa endpoints de criação de usuários
- Testa endpoints de listagem de usuários
- Testa endpoints de busca por ID
- Testa endpoints de atualização
- Testa endpoints de exclusão
- Testa controle de acesso baseado em roles (RBAC)

## Fixtures Disponíveis

- `db_session`: Sessão do banco de dados de teste
- `base_repository`: Instância do BaseRepository
- `users_repository`: Instância do UsersRepository
- `security_repository`: Instância do SecurityRepository
- `test_user`: Usuário básico de teste
- `test_admin_user`: Usuário admin de teste
- `test_super_admin_user`: Usuário superAdmin de teste
- `client`: Cliente de teste FastAPI
- `admin_token`: Token JWT para usuário admin
- `super_admin_token`: Token JWT para usuário superAdmin
- `user_token`: Token JWT para usuário básico

## Notas

- Os testes usam um banco de dados SQLite em memória
- Cada teste tem seu próprio banco de dados isolado
- As dependências do FastAPI são sobrescritas para usar o banco de teste

