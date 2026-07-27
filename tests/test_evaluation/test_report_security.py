from jinja2 import DictLoader, Environment, select_autoescape


def test_report_environment_escapes_untrusted_html() -> None:
    environment = Environment(
        loader=DictLoader({"report.html": "{{ value }}"}),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml"),
            default_for_string=True,
        ),
    )

    rendered = environment.get_template("report.html").render(
        value='<img src=x onerror="alert(1)">'
    )

    assert "<img" not in rendered
    assert "&lt;img" in rendered
