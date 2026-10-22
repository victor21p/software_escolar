"""Impede mensalidade duplicada por aluno e competência."""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("uq_cobrancas_mensalidade_aluno_competencia", "cobrancas",
                    ["aluno_id", "competencia"], unique=True,
                    postgresql_where=sa.text("tipo = 'MENSALIDADE'"))


def downgrade():
    op.drop_index("uq_cobrancas_mensalidade_aluno_competencia", table_name="cobrancas")
