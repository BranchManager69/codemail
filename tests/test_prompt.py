from codemail.prompt import build_prompt


def test_build_prompt_contains_instruction():
    prompt = build_prompt("tester@example.com", "Subject", "Body text")
    assert "structured Markdown summary" in prompt
    assert "Do not email" in prompt
