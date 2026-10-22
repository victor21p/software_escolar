from app.core.roles import Role
from app.modules.assistente import repository
from app.modules.assistente.models import Conversa
from tests.factories import make_user


def test_conversa_query_is_scoped_to_owner(db):
    owner, other = make_user(db, Role.ADMIN), make_user(db, Role.ADMIN)
    conversa = Conversa(user_id=owner.id, titulo="Privada")
    repository.add(db, conversa)
    assert repository.get_conversa(db, conversa.id, other.id) is None
    assert repository.list_conversas(db, other.id) == []
