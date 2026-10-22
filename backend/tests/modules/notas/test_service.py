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


def test_boletim_separates_years_and_deduplicates_transfers(client, db):
    from app.modules.notas.schemas import Periodo
    from app.shared.serie import Turno
    aluno = make_aluno(db)
    antiga = make_turma(db, ano_letivo=2025)
    atual = make_turma(db, ano_letivo=2026)
    transferida = make_turma(db, ano_letivo=2026, turno=Turno.TARDE)
    for turma, valor in [(antiga, 2), (atual, 8), (transferida, 10)]:
        db.add(Nota(aluno_id=aluno.id, turma_id=turma.id, disciplina="Artes",
                    periodo=Periodo.BIMESTRE_1, valor=valor, lancado_por_user_id=1))
        db.flush()
    headers = headers_of(make_user(db, Role.ADMIN))
    url = f"/api/v1/notas/alunos/{aluno.id}/boletim"
    response = client.get(url, headers=headers, params={"ano_letivo":2026})
    assert response.status_code == 200
    assert response.json()["ano_letivo"] == 2026
    assert response.json()["disciplinas"][0]["media"] == 10
    assert len(response.json()["disciplinas"][0]["notas"]) == 1
    assert client.get(url, headers=headers, params={"ano_letivo":2025}).json()["disciplinas"][0]["media"] == 2
    assert client.get(url, headers=headers, params={"ano_letivo":2024}).json()["disciplinas"] == []
