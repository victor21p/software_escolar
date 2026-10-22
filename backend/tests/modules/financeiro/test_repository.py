from app.modules.financeiro import repository


def test_empty_family_filter_has_no_charges(db):
    rows, total = repository.list_cobrancas(
        db, aluno_id=None, aluno_ids=[], status=None, limit=50, offset=0
    )
    assert rows == []
    assert total == 0
