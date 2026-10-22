from app.core.roles import Role


def test_unauthenticated_requests_are_rejected(client):
    assert client.request("POST", "/api/v1/comunicacao/avisos", json={}).status_code == 401


def test_unprivileged_student_cannot_write_or_list_staff_data(client, headers_for):
    assert (
        client.request(
            "POST", "/api/v1/comunicacao/avisos", json={}, headers=headers_for(Role.ALUNO)
        ).status_code
        == 403
    )
