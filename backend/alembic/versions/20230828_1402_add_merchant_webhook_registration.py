from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20230828_1402_add_merchant_webhook_registration'
down_revision = '826e99a35f89'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'merchant_webhook_registrations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('endpoint_id', sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column('merchant_id', sa.Integer(), sa.ForeignKey('merchants.id'), nullable=False, index=True),
        sa.Column('razorpay_webhook_id', sa.String(length=64), nullable=True),
        sa.Column('secret', sa.String(length=128), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table('merchant_webhook_registrations')
