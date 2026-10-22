import pytest
from sqlalchemy import select

from app.core.roles import Role
from app.modules.financeiro.models import Cobranca
from app.modules.matricula.schemas import StatusMatricula
from tests.factories import (
    headers_of,
    make_aluno,
    make_matricula,
    make_preco,
    make_turma,
    make_user,
)


@pytest.mark.parametrize(("valor", "esperado"), [(100, "AGUARDANDO_PAGAMENTO"), (0, "ATIVA")])
def test_approval_creates_fee_and_payment_activates_once(client, db, valor, esperado):
    aluno, turma = make_aluno(db), make_turma(db)
    matricula = make_matricula(db, aluno, turma)
    make_preco(db, turma, matricula=valor)
    headers = headers_of(make_user(db, Role.ADMIN))
    response = client.post(
        f"/api/v1/matriculas/{matricula.id}/aprovar", headers=headers, json={"turma_id": turma.id}
    )
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
    assert (
        client.post(
            f"/api/v1/matriculas/{matricula.id}/aprovar",
            headers=headers,
            json={"turma_id": turma.id},
        ).status_code
        == 409
    )


def test_approval_without_price_rolls_back_vaga(client, db):
    aluno, turma = make_aluno(db), make_turma(db)
    matricula = make_matricula(db, aluno, turma)
    headers = headers_of(make_user(db, Role.ADMIN))
    db.commit()
    response = client.post(
        f"/api/v1/matriculas/{matricula.id}/aprovar", headers=headers, json={"turma_id": turma.id}
    )
    assert response.status_code == 422
    db.rollback()
    db.refresh(turma)
    db.refresh(matricula)
    assert turma.vagas_ocupadas == 0
    assert matricula.status == StatusMatricula.EM_ANALISE
    assert db.scalar(select(Cobranca)) is None


def _payload(responsavel, *, aluno_id=None):
    from datetime import date

    payload = {"ano_letivo": date.today().year, "serie": "ANO_3", "turno": "MANHA"}
    if aluno_id:
        payload["aluno_id"] = aluno_id
    else:
        payload["aluno"] = {"nome": "Aluno de teste", "data_nascimento": "2019-05-10"}
        payload["responsaveis"] = [
            {
                "nome": responsavel.nome,
                "cpf": responsavel.cpf,
                "parentesco": "MAE",
                "responsavel_financeiro": True,
                "pode_buscar": True,
            }
        ]
    return payload


def test_family_pre_enrollment_documents_and_cancellation(client, db, tmp_path, monkeypatch):
    from app.core.config import settings
    from app.modules.auth.models import User
    from tests.factories import make_responsavel

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    resp = make_responsavel(db)
    headers = headers_of(db.get(User, resp.user_id))
    base = "/api/v1/matriculas"
    response = client.post(base, headers=headers, json=_payload(resp))
    assert response.status_code == 201
    mid = response.json()["id"]
    assert response.json()["tipo"] == "NOVA"
    assert client.get(base, headers=headers).json()["total"] == 1
    assert client.get(f"{base}/{mid}", headers=headers).status_code == 200
    url = f"{base}/{mid}/documentos/CERTIDAO_NASCIMENTO/arquivo"
    assert client.get(url, headers=headers).status_code == 404
    for name in ("primeiro.pdf", "segundo.pdf"):
        assert (
            client.post(
                url, headers=headers, files={"arquivo": (name, b"%PDF-test", "application/pdf")}
            ).status_code
            == 200
        )
    assert client.get(url, headers=headers).content == b"%PDF-test"
    other = headers_of(make_user(db, Role.RESPONSAVEL))
    assert client.get(url, headers=other).status_code == 404
    assert client.get(f"{base}/{mid}", headers=other).status_code == 404
    assert (
        client.post(
            f"{base}/{mid}/cancelar", headers=headers, json={"motivo": "Mudança de cidade"}
        ).status_code
        == 200
    )
    assert (
        client.post(url, headers=headers, files={"arquivo": ("a.pdf", b"%PDF-a")}).status_code
        == 409
    )


def test_staff_analysis_rejection_and_family_cancel_restriction(client, db):
    from app.modules.auth.models import User
    from tests.factories import make_responsavel

    resp = make_responsavel(db)
    family = headers_of(db.get(User, resp.user_id))
    admin = headers_of(make_user(db, Role.ADMIN))
    base = "/api/v1/matriculas"
    response = client.post(base, headers=family, json=_payload(resp))
    mid = response.json()["id"]
    assert client.post(f"{base}/{mid}/analise", headers=admin).status_code == 200
    assert (
        client.post(
            f"{base}/{mid}/cancelar", headers=family, json={"motivo": "Desistência"}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"{base}/{mid}/documentos/CERTIDAO_NASCIMENTO", headers=admin, json={"entregue": True}
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"{base}/{mid}/documentos/CERTIDAO_NASCIMENTO", headers=admin, json={"entregue": False}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{base}/{mid}/rejeitar", headers=admin, json={"motivo": "Documentação incompleta"}
        ).status_code
        == 200
    )
    assert (
        client.get(f"{base}/{mid}", headers=family).json()["motivo_rejeicao"]
        == "Documentação incompleta"
    )
    assert (
        client.patch(
            f"{base}/{mid}/documentos/CERTIDAO_NASCIMENTO", headers=admin, json={"entregue": True}
        ).status_code
        == 409
    )


def test_rematricula_is_unique_and_filtered_by_family(client, db):
    from app.modules.auth.models import User
    from tests.factories import make_responsavel

    resp = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[resp])
    headers = headers_of(db.get(User, resp.user_id))
    payload = _payload(resp, aluno_id=aluno.id)
    base = "/api/v1/matriculas"
    response = client.post(base, headers=headers, json=payload)
    assert response.status_code == 201
    assert response.json()["tipo"] == "REMATRICULA"
    assert client.post(base, headers=headers, json=payload).status_code == 409
    assert (
        client.get(
            base,
            headers=headers,
            params={
                "status": "PRE_MATRICULA",
                "ano_letivo": payload["ano_letivo"],
                "serie": "ANO_3",
            },
        ).json()["total"]
        == 1
    )
    outro = headers_of(make_user(db, Role.RESPONSAVEL))
    assert client.get(base, headers=outro).json()["items"] == []


def test_staff_can_cancel_approved_enrollment_and_release_vaga(client, db):
    aluno, turma = make_aluno(db), make_turma(db)
    matricula = make_matricula(db, aluno, turma)
    make_preco(db, turma)
    headers = headers_of(make_user(db, Role.ADMIN))
    url = f"/api/v1/matriculas/{matricula.id}"
    assert (
        client.post(f"{url}/aprovar", headers=headers, json={"turma_id": turma.id}).status_code
        == 200
    )
    assert turma.vagas_ocupadas == 1
    assert (
        client.post(
            f"{url}/cancelar", headers=headers, json={"motivo": "Transferência"}
        ).status_code
        == 200
    )
    assert turma.vagas_ocupadas == 0


@pytest.mark.concurrency
def test_simultaneous_approvals_consume_one_vaga_and_create_one_fee(concurrent_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy.orm import Session

    from app.core.deps import CurrentUser
    from app.core.exceptions import AppError
    from app.main import create_app
    from app.modules.matricula import service
    from app.modules.matricula.schemas import AprovarMatricula

    create_app()
    with Session(concurrent_engine, expire_on_commit=False) as setup:
        aluno, turma = make_aluno(setup), make_turma(setup)
        matricula = make_matricula(setup, aluno, turma)
        make_preco(setup, turma)
        user = make_user(setup, Role.ADMIN)
        setup.commit()
        mid, tid = matricula.id, turma.id
        actor = CurrentUser(user.id, user.role, user.email)
    barrier = Barrier(2)

    def approve():
        with Session(concurrent_engine, expire_on_commit=False) as session:
            barrier.wait(timeout=10)
            try:
                service.approve_matricula(session, mid, AprovarMatricula(turma_id=tid), actor)
                return "ok"
            except AppError:
                session.rollback()
                return "conflito"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: approve(), range(2)))
    assert sorted(results) == ["conflito", "ok"]
    from app.modules.turmas.models import Turma

    with Session(concurrent_engine) as check:
        assert check.get(Turma, tid).vagas_ocupadas == 1
        assert len(list(check.scalars(select(Cobranca)))) == 1
