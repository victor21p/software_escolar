import pytest

from app.core.exceptions import BusinessRuleError, ConflictError
from app.core.roles import Role
from app.modules.auth.models import User
from app.modules.turmas import service
from tests.factories import headers_of, make_professor, make_user


def test_turma_crud_capacity_and_teacher_assignment(client, db):
    admin = headers_of(make_user(db, Role.ADMIN))
    base = "/api/v1/turmas"
    payload = {"serie": "ANO_1", "ano_letivo": 2026, "turno": "MANHA", "capacidade": 2}
    created = client.post(base, headers=admin, json=payload)
    assert created.status_code == 201
    tid = created.json()["id"]
    assert client.post(base, headers=admin, json=payload).status_code == 409
    assert (
        len(
            client.get(
                base, headers=admin, params={"ano_letivo": 2026, "serie": "ANO_1", "ativa": True}
            ).json()
        )
        == 1
    )
    prof = make_professor(db)
    teacher = headers_of(db.get(User, prof.user_id))
    url = f"{base}/{tid}"
    assert client.get(url, headers=teacher).status_code == 404
    assert (
        client.post(f"{url}/professores", headers=admin, json={"professor_id": prof.id}).status_code
        == 200
    )
    assert len(client.get(f"{base}/minhas", headers=teacher).json()) == 1
    assert client.get(url, headers=teacher).status_code == 200
    service.occupy_vaga(db, tid)
    service.occupy_vaga(db, tid)
    with pytest.raises(ConflictError):
        service.occupy_vaga(db, tid)
    assert client.patch(url, headers=admin, json={"capacidade": 1}).status_code == 422
    service.release_vaga(db, tid)
    assert client.patch(url, headers=admin, json={"capacidade": 1}).status_code == 200
    assert client.patch(url, headers=admin, json={"ativa": False}).status_code == 200
    with pytest.raises(BusinessRuleError):
        service.occupy_vaga(db, tid)
    assert client.delete(f"{url}/professores/{prof.id}", headers=admin).status_code == 200
    assert client.delete(f"{url}/professores/{prof.id}", headers=admin).status_code == 404


def test_teacher_without_cadastro_is_rejected(client, db):
    headers = headers_of(make_user(db, Role.PROFESSOR))
    assert client.get("/api/v1/turmas/minhas", headers=headers).status_code == 403
