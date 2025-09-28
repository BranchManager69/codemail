from codemail.markdown_render import render_markdown


def test_render_markdown_wraps_in_card():
    html = render_markdown("**Hello**\n\n- item")
    assert html.startswith("<html>")
    assert "<strong>Hello</strong>" in html or "<p><strong>Hello</strong></p>" in html
