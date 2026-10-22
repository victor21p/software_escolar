"""Preserva o instante de pagamento entre gravação e leitura."""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("cobrancas", "pago_em", type_=sa.DateTime(timezone=True),
                    postgresql_using="pago_em AT TIME ZONE current_setting('TimeZone')")


def downgrade():
    op.alter_column("cobrancas", "pago_em", type_=sa.DateTime(timezone=False),
                    postgresql_using="pago_em AT TIME ZONE current_setting('TimeZone')")
