from app.core.roles import Role
from app.modules.assistente import tools


def test_all_write_tools_have_confirmation_preview_and_restricted_roles():
    for role in Role:
        for spec in tools.specs_for_role(role):
            tool = tools.get_tool(spec["function"]["name"])
            assert role in tool.roles
            if tool.mutates:
                assert tool.preview is not None


def test_nested_sensitive_fields_are_removed_from_llm_results():
    result = tools.serializar({"cpf": "segredo", "filho": {"cpf": "segredo", "nome": "Aluno"}})
    assert result == {"filho": {"nome": "Aluno"}}
