"""Cria o primeiro usuário ADMIN para destravar o login (a API não tem bootstrap).

Uso:
    uv run python -m scripts.seed_admin
    # ou, dentro do container:
    docker compose exec api python -m scripts.seed_admin

Idempotente: se já existir um usuário com o e-mail abaixo, não faz nada.
"""

import os
from getpass import getpass

from pydantic import TypeAdapter

from app.core.database import SessionLocal
from app.core.roles import Role
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.auth.schemas import Password

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@semeando.edu.br")
ADMIN_NOME = "Admin Semeando"


def main() -> None:
    with SessionLocal() as db:
        existente = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existente:
            print(f"Usuário {ADMIN_EMAIL} já existe (id={existente.id}). Nada a fazer.")
            return

        password = os.environ.get("ADMIN_PASSWORD") or getpass("Senha inicial do administrador: ")
        TypeAdapter(Password).validate_python(password)
        admin = User(
            email=ADMIN_EMAIL,
            nome=ADMIN_NOME,
            password_hash=hash_password(password),
            role=Role.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin criado: {ADMIN_EMAIL}")


if __name__ == "__main__":
    main()
