import pytest
from sqlalchemy import select
from app.core.roles import Role
from app.modules.financeiro.models import Cobranca
from app.modules.matricula.schemas import StatusMatricula
from app.shared.serie import Serie
from tests.factories import headers_of, make_user, make_aluno, make_turma, make_matricula, make_preco


def test_monthly_charges_require_active_enrollment_and_correct_price(client, db):
    aluno, sem_matricula = make_aluno(db), make_aluno(db)
    turma = make_turma(db)
    outra_turma = make_turma(db, serie=Serie.ANO_1)
    make_preco(db, outra_turma, mensalidade=300)
    make_preco(db, turma, mensalidade=900)
    make_matricula(db, aluno, turma, status=StatusMatricula.ATIVA)
    headers = headers_of(make_user(db, Role.FINANCEIRO))
    url = "/api/v1/financeiro/cobrancas/gerar-mensalidades"
    response = client.post(url, headers=headers, params={"competencia":f"{turma.ano_letivo}-12"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["aluno_id"] == aluno.id
    assert float(response.json()[0]["valor_final"]) == 900
    assert client.post(url, headers=headers, params={"competencia":f"{turma.ano_letivo}-12"}).json() == []
    assert sem_matricula.id not in [c.aluno_id for c in db.scalars(select(Cobranca))]


@pytest.mark.parametrize("competencia", ["2026-00", "2026-13", "2026-1"])
def test_invalid_month_is_rejected(client, db, competencia):
    headers = headers_of(make_user(db, Role.ADMIN))
    assert client.post("/api/v1/financeiro/cobrancas/gerar-mensalidades", headers=headers,
                       params={"competencia":competencia}).status_code == 422
