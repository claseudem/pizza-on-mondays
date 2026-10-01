from ui import TITLE_COLOR, colored_subheader, colored_title


def test_colored_title_renders_h1_with_title_color(mocker):
    markdown = mocker.patch("ui.st.markdown")
    colored_title("🍕 Pizza on Mondays")
    markdown.assert_called_once()
    html, kwargs = markdown.call_args
    assert "<h1" in html[0]
    assert TITLE_COLOR in html[0]
    assert "🍕 Pizza on Mondays" in html[0]
    assert kwargs["unsafe_allow_html"] is True


def test_colored_subheader_renders_h3_with_title_color(mocker):
    markdown = mocker.patch("ui.st.markdown")
    colored_subheader("Resumen")
    markdown.assert_called_once()
    html, kwargs = markdown.call_args
    assert "<h3" in html[0]
    assert TITLE_COLOR in html[0]
    assert "Resumen" in html[0]
    assert kwargs["unsafe_allow_html"] is True
