from sqlalchemy import select
from app.core.roles import Role
from app.modules.notas.models import Nota
from app.modules.matricula.schemas import StatusMatricula
from tests.factories import headers_of, make_user, make_aluno, make_turma, make_matricula


def test_notes_require_active_enrollment_even_for_admin(client, db):
    aluno, turma = make_aluno(db), make_turma(db)
    headers = headers_of(make_user(db, Role.ADMIN))
    url = f"/api/v1/notas/turmas/{turma.id}/alunos/{aluno.id}"
    payload = {"disciplina":"Artes", "periodo":"BIMESTRE_1", "valor":8}
    assert client.put(url, headers=headers, json=payload).status_code == 404
    assert db.scalar(select(Nota)) is None
    matricula = make_matricula(db, aluno, turma, status=StatusMatricula.ATIVA)
    assert client.put(url, headers=headers, json=payload).status_code == 200
    matricula.status = StatusMatricula.CANCELADA
    db.flush()
    payload["valor"] = 2
    assert client.put(url, headers=headers, json=payload).status_code == 404
    assert float(db.scalar(select(Nota)).valor) == 8
