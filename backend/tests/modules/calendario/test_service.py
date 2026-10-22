from datetime import date, timedelta

import pytest

from app.core.exceptions import NotFoundError
from app.core.roles import Role
from app.modules.auth.models import User
from app.modules.calendario import service
from app.modules.turmas.models import TurmaProfessor
from tests.factories import headers_of, make_professor, make_turma, make_user


def test_calendar_crud_interval_and_ownership(client, db):
    admin = headers_of(make_user(db, Role.ADMIN))
    turma = make_turma(db)
    prof = make_professor(db)
    db.add(TurmaProfessor(turma_id=turma.id, professor_id=prof.id))
    db.flush()
    teacher = headers_of(db.get(User, prof.user_id))
    base = "/api/v1/calendario/eventos"
    payload = {"titulo": "Prova", "data_inicio": str(date.today()), "tipo": "PROVA"}
    assert client.post(base, headers=teacher, json=payload).status_code == 403
    payload["turma_id"] = turma.id
    created = client.post(base, headers=teacher, json=payload)
    assert created.status_code == 201
    eid = created.json()["id"]
    assert service.get_evento(db, eid).titulo == "Prova"
    assert len(client.get(base, headers=admin, params={"turma_id": turma.id}).json()) == 1
    assert (
        client.patch(f"{base}/{eid}", headers=teacher, json={"titulo": "Prova nova"}).status_code
        == 200
    )
    other = headers_of(make_user(db, Role.PROFESSOR))
    assert (
        client.patch(f"{base}/{eid}", headers=other, json={"titulo": "Inválido"}).status_code == 403
    )
    assert client.delete(f"{base}/{eid}", headers=other).status_code == 403
    assert client.delete(f"{base}/{eid}", headers=admin).status_code == 204
    with pytest.raises(NotFoundError):
        service.get_evento(db, eid)
    payload.pop("turma_id")
    payload["data_fim"] = str(date.today() + timedelta(days=2))
    created = client.post(base, headers=admin, json=payload)
    assert created.status_code == 201
    eid = created.json()["id"]
    assert (
        client.patch(
            f"{base}/{eid}",
            headers=admin,
            json={"data_inicio": str(date.today() + timedelta(days=3))},
        ).status_code
        == 422
    )
