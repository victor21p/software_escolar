import pytest
from sqlalchemy import select

from app.core.roles import Role
from app.modules.financeiro.models import Cobranca
from app.modules.matricula.schemas import StatusMatricula
from app.shared.serie import Serie
from tests.factories import (
    headers_of,
    make_aluno,
    make_matricula,
    make_preco,
    make_turma,
    make_user,
)


def test_monthly_charges_require_active_enrollment_and_correct_price(client, db):
    aluno, sem_matricula = make_aluno(db), make_aluno(db)
    turma = make_turma(db)
    outra_turma = make_turma(db, serie=Serie.ANO_1)
    make_preco(db, outra_turma, mensalidade=300)
    make_preco(db, turma, mensalidade=900)
    make_matricula(db, aluno, turma, status=StatusMatricula.ATIVA)
    headers = headers_of(make_user(db, Role.FINANCEIRO))
    url = "/api/v1/financeiro/cobrancas/gerar-mensalidades"
    response = client.post(url, headers=headers, params={"competencia": f"{turma.ano_letivo}-12"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["aluno_id"] == aluno.id
    assert float(response.json()[0]["valor_final"]) == 900
    assert (
        client.post(url, headers=headers, params={"competencia": f"{turma.ano_letivo}-12"}).json()
        == []
    )
    assert sem_matricula.id not in [c.aluno_id for c in db.scalars(select(Cobranca))]


@pytest.mark.parametrize("competencia", ["2026-00", "2026-13", "2026-1"])
def test_invalid_month_is_rejected(client, db, competencia):
    headers = headers_of(make_user(db, Role.ADMIN))
    assert (
        client.post(
            "/api/v1/financeiro/cobrancas/gerar-mensalidades",
            headers=headers,
            params={"competencia": competencia},
        ).status_code
        == 422
    )


def test_listing_does_not_clear_debt_or_write_status(client, db):
    from datetime import date, timedelta

    from app.modules.financeiro import service
    from app.modules.financeiro.models import StatusCobranca, TipoCobranca

    aluno = make_aluno(db)
    charge = Cobranca(
        aluno_id=aluno.id,
        tipo=TipoCobranca.TAXA_EXTRA,
        valor_original=100,
        valor_final=100,
        valor_desconto=0,
        vencimento=date.today() - timedelta(days=30),
        status=StatusCobranca.PENDENTE,
    )
    db.add(charge)
    db.flush()
    headers = headers_of(make_user(db, Role.ADMIN))
    assert service.is_aluno_inadimplente(db, aluno.id)
    response = client.get(
        "/api/v1/financeiro/cobrancas", headers=headers, params={"status": "ATRASADA"}
    )
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "ATRASADA"
    db.refresh(charge)
    assert charge.status == StatusCobranca.PENDENTE
    assert service.is_aluno_inadimplente(db, aluno.id)
    assert (
        client.get(
            "/api/v1/financeiro/cobrancas", headers=headers, params={"status": "PENDENTE"}
        ).json()["total"]
        == 0
    )
    charge.status = StatusCobranca.ATRASADA
    db.flush()
    assert service.is_aluno_inadimplente(db, aluno.id)
    charge.status = StatusCobranca.PAGA
    db.flush()
    assert not service.is_aluno_inadimplente(db, aluno.id)


def test_financial_scholarship_price_and_manual_charge_workflow(client, db):
    from datetime import date

    headers = headers_of(make_user(db, Role.FINANCEIRO))
    aluno = make_aluno(db)
    base = "/api/v1/financeiro"
    bolsa = client.post(
        f"{base}/bolsas",
        headers=headers,
        json={
            "aluno_id": aluno.id,
            "percentual_desconto": 25,
            "motivo": "Bolsa social",
            "vigencia_inicio": str(date.today()),
        },
    )
    assert bolsa.status_code == 201
    bid = bolsa.json()["id"]
    assert (
        client.patch(
            f"{base}/bolsas/{bid}", headers=headers, json={"percentual_desconto": 50}
        ).status_code
        == 200
    )
    assert (
        len(client.get(f"{base}/bolsas", headers=headers, params={"aluno_id": aluno.id}).json())
        == 1
    )
    preco = client.post(
        f"{base}/precos",
        headers=headers,
        json={
            "serie": "ANO_3",
            "ano_letivo": 2026,
            "valor_matricula": 100,
            "valor_mensalidade": 800,
        },
    )
    assert preco.status_code == 201
    pid = preco.json()["id"]
    assert (
        client.patch(
            f"{base}/precos/{pid}", headers=headers, json={"valor_mensalidade": 900}
        ).status_code
        == 200
    )
    assert len(client.get(f"{base}/precos", headers=headers).json()) == 1
    charge = client.post(
        f"{base}/cobrancas",
        headers=headers,
        json={
            "aluno_id": aluno.id,
            "tipo": "TAXA_EXTRA",
            "valor_original": 50,
            "vencimento": str(date.today()),
        },
    )
    assert charge.status_code == 201
    assert (
        client.post(
            f"{base}/cobrancas/{charge.json()['id']}/marcar-paga", headers=headers
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"{base}/precos/999999", headers=headers, json={"valor_mensalidade": 1}
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"{base}/bolsas/999999", headers=headers, json={"percentual_desconto": 1}
        ).status_code
        == 404
    )


@pytest.mark.concurrency
def test_simultaneous_monthly_generation_is_idempotent(concurrent_engine):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy.orm import Session

    from app.modules.financeiro import service

    with Session(concurrent_engine, expire_on_commit=False) as setup:
        aluno, turma = make_aluno(setup), make_turma(setup)
        make_matricula(setup, aluno, turma, status=StatusMatricula.ATIVA)
        make_preco(setup, turma)
        competencia = f"{turma.ano_letivo}-12"
        setup.commit()
    barrier = Barrier(2)

    def generate():
        with Session(concurrent_engine, expire_on_commit=False) as session:
            barrier.wait(timeout=10)
            return len(service.gerar_mensalidades(session, competencia))

    with ThreadPoolExecutor(max_workers=2) as pool:
        counts = list(pool.map(lambda _: generate(), range(2)))
    assert sum(counts) == 1
    with Session(concurrent_engine) as check:
        assert len(list(check.scalars(select(Cobranca)))) == 1


def test_financial_audit_records_actor_before_after_and_no_duplicate_payment(client, db):
    from datetime import date

    from app.core.audit import AuditLog

    actor = make_user(db, Role.FINANCEIRO)
    headers = headers_of(actor)
    aluno = make_aluno(db)
    base = "/api/v1/financeiro"
    bolsa = client.post(
        f"{base}/bolsas",
        headers=headers,
        json={
            "aluno_id": aluno.id,
            "percentual_desconto": 25,
            "motivo": "Apoio",
            "vigencia_inicio": str(date.today()),
        },
    )
    bid = bolsa.json()["id"]
    assert (
        client.patch(
            f"{base}/bolsas/{bid}", headers=headers, json={"percentual_desconto": 50}
        ).status_code
        == 200
    )
    logs = list(
        db.scalars(select(AuditLog).where(AuditLog.entity == "bolsa").order_by(AuditLog.id))
    )
    assert len(logs) == 2
    assert logs[0].actor_user_id == actor.id
    assert logs[0].before is None
    assert float(logs[1].before["percentual_desconto"]) == 25
    assert float(logs[1].after["percentual_desconto"]) == 50
    charge = client.post(
        f"{base}/cobrancas",
        headers=headers,
        json={
            "aluno_id": aluno.id,
            "tipo": "TAXA_EXTRA",
            "valor_original": 125,
            "vencimento": str(date.today()),
        },
    )
    cid = charge.json()["id"]
    for _ in range(2):
        assert (
            client.post(f"{base}/cobrancas/{cid}/marcar-paga", headers=headers).status_code == 200
        )
    payments = list(db.scalars(select(AuditLog).where(AuditLog.action == "cobranca.pagar")))
    assert len(payments) == 1
    assert payments[0].actor_user_id == actor.id
    assert payments[0].before["status"] == "PENDENTE"
    assert payments[0].after["status"] == "PAGA"
    assert payments[0].after["origem"] == "manual"


def test_signed_webhook_is_audited_as_system_and_replay_is_idempotent(client, db):
    import hashlib
    import hmac
    import json
    from datetime import date

    from app.core.audit import AuditLog
    from app.core.config import settings

    aluno = make_aluno(db)
    headers = headers_of(make_user(db, Role.ADMIN))
    charge = client.post(
        "/api/v1/financeiro/cobrancas",
        headers=headers,
        json={
            "aluno_id": aluno.id,
            "tipo": "TAXA_EXTRA",
            "valor_original": 100,
            "vencimento": str(date.today()),
        },
    )
    body = json.dumps({"cobranca_id": charge.json()["id"]}).encode()
    signature = hmac.new(settings.payment_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    url = "/api/v1/financeiro/webhook"
    assert client.post(url, content=body).status_code == 401
    for _ in range(2):
        assert (
            client.post(
                url,
                content=body,
                headers={"X-Signature": signature, "Content-Type": "application/json"},
            ).status_code
            == 200
        )
    entries = list(db.scalars(select(AuditLog).where(AuditLog.action == "cobranca.pagar")))
    assert len(entries) == 1
    assert entries[0].actor_user_id is None
    assert entries[0].actor_role == "SISTEMA"
    assert entries[0].after["origem"] == "webhook"
