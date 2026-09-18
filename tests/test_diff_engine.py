import pytest
from core.diff_engine import DiffEngine, DiffStats

def test_diff_engine_plain_text_extraction():
    html_raw = "<h1>Capítulo 1</h1><p>El bosque era <b>oscuro</b> y profundo.</p>"
    text = DiffEngine.html_to_plain_text(html_raw)
    assert "Capítulo 1" in text
    assert "El bosque era oscuro y profundo." in text

def test_diff_engine_identical_texts():
    text = "Había una vez en un reino muy lejano."
    diff_html, stats = DiffEngine.compute_inline_diff_html(text, text, is_dark=True)
    
    assert "<ins" not in diff_html
    assert "<del" not in diff_html
    assert stats.words_added == 0
    assert stats.words_deleted == 0
    assert stats.words_unchanged > 0

def test_diff_engine_additions_and_deletions():
    old_text = "El caballero montó su caballo blanco."
    new_text = "El caballero valiente montó su corcel negro."
    
    diff_html, stats = DiffEngine.compute_inline_diff_html(old_text, new_text, is_dark=False)
    
    assert "<ins" in diff_html
    assert "<del" in diff_html
    assert "caballo" in diff_html
    assert "corcel" in diff_html
    assert stats.words_added > 0
    assert stats.words_deleted > 0
