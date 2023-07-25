"""Add post Model

Revision ID: 47c9b98ac39f
Revises: 66f4cfb18256
Create Date: 2023-07-25 11:39:01.061349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47c9b98ac39f'
down_revision = '66f4cfb18256'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('author', sa.String(length=255), nullable=True),
    sa.Column('date_posted', sa.DateTime(), nullable=True),
    sa.Column('slug', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('posts')
    # ### end Alembic commands ###