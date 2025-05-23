"""Add cancel_at_period_end to StripeCustomer

Revision ID: ceec0b4d2e59
Revises: 
Create Date: 2024-07-22 22:49:00.217379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ceec0b4d2e59'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('stripe_customer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cancel_at_period_end', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('stripe_customer', schema=None) as batch_op:
        batch_op.drop_column('cancel_at_period_end')

    # ### end Alembic commands ###
