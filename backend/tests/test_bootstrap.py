from contextlib import contextmanager

from sqlalchemy import select

from app.core.security import verify_password
from app.modules.auth.models import User
from scripts import seed_admin


def test_admin_bootstrap_is_idempotent_and_does_not_print_password(db, monkeypatch, capsys):
    @contextmanager
    def session():
        yield db

    monkeypatch.setattr(seed_admin, "SessionLocal", session)
    monkeypatch.setenv("ADMIN_PASSWORD", "Bootstrap1234")
    seed_admin.main()
    seed_admin.main()
    users = list(db.scalars(select(User)))
    assert len(users) == 1
    assert verify_password("Bootstrap1234", users[0].password_hash)
    assert "Bootstrap1234" not in capsys.readouterr().out
