from datetime import date

from app.core.roles import Role
from app.modules.matricula.schemas import StatusMatricula
from tests.factories import headers_of, make_aluno, make_matricula, make_turma, make_user


def test_attendance_correction_history_and_family_isolation(client, db):
    aluno, turma = make_aluno(db), make_turma(db)
    make_matricula(db, aluno, turma, status=StatusMatricula.ATIVA)
    headers = headers_of(make_user(db, Role.ADMIN))
    base = f"/api/v1/frequencia/turmas/{turma.id}"
    assert client.get(base, headers=headers).json()[0]["lancado"] is False
    data = {"registros": [{"aluno_id": aluno.id, "status": "PRESENTE"}]}
    assert client.post(base, headers=headers, json=data).status_code == 200
    assert client.get(base, headers=headers).json()[0]["lancado"] is True
    assert client.post(base, headers=headers, json=data).status_code == 200
    assert (
        client.patch(
            f"{base}/alunos/{aluno.id}", headers=headers, json={"status": "FALTA"}
        ).status_code
        == 200
    )
    params = {"de": str(date.today()), "ate": str(date.today())}
    url = f"/api/v1/frequencia/alunos/{aluno.id}"
    historico = client.get(url, headers=headers, params=params).json()
    assert historico["percentual_presenca"] == 0
    assert len(historico["registros"]) == 1
    outro = headers_of(make_user(db, Role.RESPONSAVEL))
    assert client.get(url, headers=outro, params=params).status_code == 404
    assert (
        client.patch(f"{base}/alunos/999999", headers=headers, json={"status": "FALTA"}).status_code
        == 404
    )
