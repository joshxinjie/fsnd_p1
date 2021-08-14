"""empty message

Revision ID: c58b17c85642
Revises: 22a0a322076e
Create Date: 2021-08-08 16:47:16.581374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c58b17c85642'
down_revision = '22a0a322076e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('website_link', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'website_link')
    # ### end Alembic commands ###