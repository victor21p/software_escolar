# Semeando — gestão escolar

API FastAPI/PostgreSQL e quatro aplicações React/TypeScript: administração, responsável,
aluno e professor. Inclui matrícula, financeiro, frequência, boletim, calendário,
comunicação e assistente opcional com confirmação das alterações.

## Executar com Docker

Requer Docker Engine com Compose v2.

1. Copie `.env.example` para `.env`.
2. Defina `SECRET_KEY` e `PAYMENT_WEBHOOK_SECRET` próprios. Por exemplo, gere cada segredo
   com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. Execute `docker compose up -d --build --wait`.
4. Crie o administrador: `docker compose exec api python -m scripts.seed_admin`.
   O comando pede a senha inicial e não a imprime. `ADMIN_EMAIL` pode alterar o e-mail.

| Interface | Endereço local |
|---|---|
| Administração | http://localhost:8080 |
| Responsável | http://localhost:8081 |
| Aluno | http://localhost:8082 |
| Professor | http://localhost:8083 |
| Documentação da API | http://localhost:8000/api/docs |

Cada interface encaminha `/api` para a API pelo Nginx. Assim, o navegador funciona
também a partir de outro computador, sem apontar a API para o localhost do visitante.
O PostgreSQL e a porta direta da API ficam restritos ao host. As migrations são
aplicadas antes da inicialização da API e o healthcheck controla a subida das interfaces.

`DEEPSEEK_API_KEY` é opcional: sem ela, o chat informa indisponibilidade e os outros
módulos continuam operando. Uma chave previamente exposta deve ser revogada no provedor;
removê-la do código não a revoga. Não há gateway bancário real configurado por padrão.

## Desenvolvimento local

Use Python 3.12, uv, Node 22 e PostgreSQL 16. Inicie o banco com `docker compose up -d db`.
Em `backend/`, use `uv sync --frozen`, `uv run alembic upgrade head` e
`uv run uvicorn app.main:app --reload`. Em cada aplicação, execute `npm ci` e `npm run dev`.
O Vite encaminha `/api` para a API local; `VITE_API_URL` permite uma URL alternativa.

## Verificações

No backend: `uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy app tests` e `uv run pytest --cov=app --cov-fail-under=80`.
Nos quatro frontends: `npm run lint`, `npm run typecheck`, `npm test` e `npm run build`.

O banco de testes é descartável: configure `TEST_DATABASE_URL` apontando exclusivamente
para ele, pois a suíte recria seu schema. Pelo Compose:
`docker compose --profile test run --rm tests`.

O CI verifica os quatro frontends, a API com PostgreSQL 16 e uma instalação Docker.
Antes de implantar, faça backup e resolva mensalidades duplicadas existentes: a migration
0007 cria unicidade por aluno/competência e recusa dados que violem essa regra.

## Implantação

Use HTTPS no domínio público, `ENVIRONMENT=production`, segredos próprios e
`REFRESH_COOKIE_SECURE=true`. Se trocar a senha do banco no Compose, use uma senha
compatível com URL. Valores com caracteres reservados exigem adaptar a URL de conexão
com codificação percent-encoded para a API e o serviço de testes.
Backups devem incluir o banco e o volume `uploads`. Dados e contas de demonstração
devem ficar no ambiente de desenvolvimento.

Consulte [a arquitetura](docs/ARQUITETURA.md), [o fluxo de contribuição](docs/CONTRIBUINDO.md)
e [as regras do boletim](docs/modulos/notas.md).
