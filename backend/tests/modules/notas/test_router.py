from app.core.roles import Role


def test_unauthenticated_requests_are_rejected(client):
    assert client.request("PUT", "/api/v1/notas/turmas/1/alunos/1", json={}).status_code == 401


def test_unprivileged_student_cannot_write_or_list_staff_data(client, headers_for):
    assert (
        client.request(
            "PUT", "/api/v1/notas/turmas/1/alunos/1", json={}, headers=headers_for(Role.ALUNO)
        ).status_code
        == 403
    )
