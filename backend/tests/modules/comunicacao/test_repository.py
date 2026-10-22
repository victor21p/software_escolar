from app.modules.comunicacao import repository


def test_empty_visible_audiences_return_no_notices(db):
    rows, total = repository.list_avisos_visiveis(
        db, ve_tudo=False, publicos=[], turma_ids=[], limit=50, offset=0
    )
    assert rows == []
    assert total == 0
