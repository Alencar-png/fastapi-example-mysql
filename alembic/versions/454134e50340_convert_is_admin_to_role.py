"""convert_is_admin_to_role

Revision ID: 454134e50340
Revises: c3d2c28b645d
Create Date: 2026-01-08 14:36:11.022657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '454134e50340'
down_revision: Union[str, None] = 'c3d2c28b645d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Verificar se a coluna is_admin existe (se não existir, a tabela já foi atualizada)
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'is_admin' not in columns:
        # A tabela já foi criada com role, não precisa fazer nada
        return
    
    # Criar o enum UserRole (MySQL cria o enum diretamente na coluna)
    userrole_enum = sa.Enum('superAdmin', 'admin', 'basicUser', name='userrole')
    
    # Verificar se role já existe antes de adicionar
    if 'role' not in columns:
        # Adicionar coluna role (temporariamente nullable)
        op.add_column('users', sa.Column('role', userrole_enum, nullable=True))
    
    # Migrar dados: is_admin=True -> role='admin', is_admin=False -> role='basicUser'
    op.execute("""
        UPDATE users 
        SET role = CASE 
            WHEN is_admin = 1 THEN 'admin'
            ELSE 'basicUser'
        END
        WHERE role IS NULL
    """)
    
    # Tornar role NOT NULL (MySQL requer especificar o tipo existente)
    op.alter_column('users', 'role',
                    existing_type=userrole_enum,
                    nullable=False)
    
    # Remover coluna is_admin
    op.drop_column('users', 'is_admin')


def downgrade() -> None:
    # Verificar se a coluna role existe
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'role' not in columns:
        # A tabela não tem role, não precisa fazer nada
        return
    
    # Adicionar coluna is_admin se não existir
    if 'is_admin' not in columns:
        op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    
    # Migrar dados: role='admin' ou role='superAdmin' -> is_admin=True, outros -> is_admin=False
    op.execute("""
        UPDATE users 
        SET is_admin = CASE 
            WHEN role IN ('admin', 'superAdmin') THEN 1
            ELSE 0
        END
        WHERE is_admin IS NULL
    """)
    
    # Tornar is_admin NOT NULL (MySQL requer especificar o tipo existente)
    op.alter_column('users', 'is_admin',
                    existing_type=sa.Boolean(),
                    nullable=False)
    
    # Remover coluna role (MySQL remove o enum automaticamente)
    op.drop_column('users', 'role')
