import pytest
from sqlalchemy import select

from app.core.roles import Role
from app.modules.financeiro.models import Cobranca
from app.modules.matricula.schemas import StatusMatricula
from tests.factories import headers_of, make_user, make_aluno, make_turma, make_matricula, make_preco


@pytest.mark.parametrize("valor,esperado", [(100, "AGUARDANDO_PAGAMENTO"), (0, "ATIVA")])
def test_approval_creates_fee_and_payment_activates_once(client, db, valor, esperado):
    aluno, turma = make_aluno(db), make_turma(db)
    matricula = make_matricula(db, aluno, turma)
    make_preco(db, turma, matricula=valor)
    headers = headers_of(make_user(db, Role.ADMIN))
    response = client.post(f"/api/v1/matriculas/{matricula.id}/aprovar",
                           headers=headers, json={"turma_id":turma.id})
    assert response.status_code == 200
    assert response.json()["status"] == esperado
    cobranca = db.scalar(select(Cobranca).where(Cobranca.matricula_id == matricula.id))
    assert cobranca.aluno_id == aluno.id
    url = f"/api/v1/financeiro/cobrancas/{cobranca.id}/marcar-paga"
    assert client.post(url, headers=headers).status_code == 200
    primeiro_pagamento = cobranca.pago_em
    assert client.post(url, headers=headers).status_code == 200
    assert cobranca.pago_em == primeiro_pagamento
    assert matricula.status == StatusMatricula.ATIVA
    assert turma.vagas_ocupadas == 1
    assert client.post(f"/api/v1/matriculas/{matricula.id}/aprovar",
                       headers=headers, json={"turma_id":turma.id}).status_code == 409


def test_approval_without_price_rolls_back_vaga(client, db):
    aluno, turma = make_aluno(db), make_turma(db)
    matricula = make_matricula(db, aluno, turma)
    headers = headers_of(make_user(db, Role.ADMIN))
    response = client.post(f"/api/v1/matriculas/{matricula.id}/aprovar",
                           headers=headers, json={"turma_id":turma.id})
    assert response.status_code == 422
    db.rollback()
