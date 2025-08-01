"""Add is_admin field to User model

Revision ID: 7131b24c7ecd
Revises: 2862d1a8d786
Create Date: 2025-07-29 13:45:12.189539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7131b24c7ecd'
down_revision = '2862d1a8d786'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        # [수정 또는 추가할 코드 시작]
        # SQLite 호환성을 위해 server_default 값을 '0' (False)으로 명시적으로 지정합니다.
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
        # [수정 또는 추가할 코드 끝]

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')

    # ### end Alembic commands ###