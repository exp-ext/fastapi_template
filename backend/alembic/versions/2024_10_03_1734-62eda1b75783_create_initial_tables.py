"""Create initial tables

Revision ID: 62eda1b75783
Revises: 
Create Date: 2024-10-03 17:34:12.621988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62eda1b75783'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('images',
    sa.Column('file', sa.String(), nullable=True),
    sa.Column('is_main', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_images_id'), 'images', ['id'], unique=False)
    op.create_table('tg_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('link', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tg_groups_chat_id'), 'tg_groups', ['chat_id'], unique=True)
    op.create_index(op.f('ix_tg_groups_id'), 'tg_groups', ['id'], unique=False)
    op.create_table('tg_users',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('is_blocked_bot', sa.Boolean(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_tg_group_association',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['tg_groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['tg_users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'group_id')
    )
    op.create_table('users',
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('tg_user_id', sa.BigInteger(), nullable=True),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('hashed_password', sa.String(length=1024), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['tg_user_id'], ['tg_users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tg_user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('user_image_association',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('image_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['image_id'], ['images.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'image_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_image_association')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('user_tg_group_association')
    op.drop_table('tg_users')
    op.drop_index(op.f('ix_tg_groups_id'), table_name='tg_groups')
    op.drop_index(op.f('ix_tg_groups_chat_id'), table_name='tg_groups')
    op.drop_table('tg_groups')
    op.drop_index(op.f('ix_images_id'), table_name='images')
    op.drop_table('images')
    # ### end Alembic commands ###
