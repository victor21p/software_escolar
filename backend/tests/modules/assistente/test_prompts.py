from app.core.deps import CurrentUser
from app.core.roles import Role
from app.modules.assistente import prompts


def test_prompt_preserves_user_identity_and_confirmation_requirement():
    prompt = prompts.system_prompt(CurrentUser(1, Role.RESPONSAVEL, "teste@example.com"))
    assert "RESPONSAVEL" in prompt
    assert "confirm" in prompt.lower()
