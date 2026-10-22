import pytest

from app.core.roles import Role
from app.modules.auth.models import User
from app.modules.matricula.schemas import StatusMatricula
from app.modules.turmas.models import TurmaProfessor
from tests.factories import (
    headers_of,
    make_aluno,
    make_matricula,
    make_professor,
    make_responsavel,
    make_turma,
    make_user,
)


@pytest.fixture
def forum(db):
    responsavel = make_responsavel(db)
    aluno = make_aluno(db, responsaveis=[responsavel])
    aluno_user = make_user(db, Role.ALUNO)
    aluno.user_id = aluno_user.id
    turma = make_turma(db)
    professor = make_professor(db)
    db.add(TurmaProfessor(turma_id=turma.id, professor_id=professor.id))
    matricula = make_matricula(db, aluno, turma, status=StatusMatricula.ATIVA)
    return (
        turma,
        matricula,
        {
            "professor": headers_of(db.get(User, professor.user_id)),
            "responsavel": headers_of(db.get(User, responsavel.user_id)),
            "aluno": headers_of(aluno_user),
            "outro": headers_of(make_user(db, Role.RESPONSAVEL)),
            "admin": headers_of(make_user(db, Role.ADMIN)),
        },
    )


def test_turma_notice_reaches_its_family_and_read_count_is_isolated(client, db, forum):
    turma, matricula, headers = forum
    base = "/api/v1/comunicacao/avisos"
    response = client.post(
        base,
        headers=headers["professor"],
        json={"titulo": "Prova", "corpo": "Amanhã", "publico_alvo": "TURMA", "turma_id": turma.id},
    )
    assert response.status_code == 201
    aviso_id = response.json()["id"]
    for role in ("responsavel", "aluno", "professor", "admin"):
        assert client.get(base, headers=headers[role]).json()["total"] == 1
    assert client.get(base, headers=headers["outro"]).json()["total"] == 0
    assert client.post(f"{base}/{aviso_id}/lido", headers=headers["outro"]).status_code == 404
    for _ in range(2):
        assert (
            client.post(f"{base}/{aviso_id}/lido", headers=headers["responsavel"]).status_code
            == 204
        )
    assert (
        client.get(f"{base}/nao-lidos/total", headers=headers["responsavel"]).json()["total"] == 0
    )
    assert client.get(f"{base}/nao-lidos/total", headers=headers["aluno"]).json()["total"] == 1
    matricula.status = StatusMatricula.CANCELADA
    db.flush()
    assert client.get(base, headers=headers["responsavel"]).json()["total"] == 0


def test_professor_cannot_expand_notice_audience_or_move_to_foreign_turma(client, db, forum):
    from app.shared.serie import Serie

    turma, _, headers = forum
    base = "/api/v1/comunicacao/avisos"
    response = client.post(
        base,
        headers=headers["professor"],
        json={"titulo": "Prova", "corpo": "Amanhã", "publico_alvo": "TURMA", "turma_id": turma.id},
    )
    url = f"{base}/{response.json()['id']}"
    assert (
        client.patch(
            url, headers=headers["professor"], json={"publico_alvo": "TODOS", "turma_id": None}
        ).status_code
        == 403
    )
    outra = make_turma(db, serie=Serie.ANO_1)
    assert (
        client.patch(url, headers=headers["professor"], json={"turma_id": outra.id}).status_code
        == 403
    )
    assert (
        client.patch(url, headers=headers["professor"], json={"titulo": "Nova prova"}).status_code
        == 200
    )
    assert client.patch(url, headers=headers["outro"], json={"titulo": "Outro"}).status_code == 403
    assert client.delete(url, headers=headers["outro"]).status_code == 403
    assert client.delete(url, headers=headers["professor"]).status_code == 204
