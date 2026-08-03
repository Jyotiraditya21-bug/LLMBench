from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_has_accessible_progress_and_cancellation() -> None:
    html = (ROOT / "backend/app/static/index.html").read_text()

    assert 'class="skip-link"' in html
    assert 'role="progressbar"' in html
    assert 'aria-live="polite"' in html
    assert 'id="hub-cancel-button"' in html


def test_dashboard_uses_paginated_results_and_safe_error_text() -> None:
    script = (ROOT / "backend/app/static/app.js").read_text()

    assert "/results?limit=100" in script
    assert "cancelActiveRun" in script
    assert "msgEl.textContent = `Run failed:" in script
    assert "msgEl.innerHTML = `<span" not in script
