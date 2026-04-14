"""Tests for utils.py — slugify, strip_preamble, check_report_structure, constants."""

from utils import (
    DEFAULT_MODEL, DEFAULT_PERMISSION_MODE, DEFAULT_TOOLS,
    check_report_structure, slugify, strip_preamble,
)


# --- slugify ---

def test_slugify_basic():
    assert slugify("State of AI Coding Agents 2026") == "state-of-ai-coding-agents-2026"


def test_slugify_special_chars():
    assert slugify("n8n vs Make.com vs Zapier!") == "n8n-vs-makecom-vs-zapier"


def test_slugify_german_umlauts():
    assert slugify("KI-Telefonie im DACH-Mittelstand") == "ki-telefonie-im-dach-mittelstand"


def test_slugify_whitespace_normalization():
    assert slugify("  lots   of   spaces  ") == "lots-of-spaces"


def test_slugify_truncates_at_80():
    long_text = "a " * 100
    result = slugify(long_text)
    assert len(result) <= 80


def test_slugify_empty_string():
    assert slugify("") == ""


# --- strip_preamble ---

def test_strip_preamble_removes_artifact(sample_report_with_preamble):
    result = strip_preamble(sample_report_with_preamble)
    assert result.startswith("## Research Plan")
    assert "PAI" not in result


def test_strip_preamble_preserves_clean_markdown():
    clean = "## Report\n\nContent here."
    assert strip_preamble(clean) == clean


def test_strip_preamble_preserves_table_start():
    text = "Some preamble\n| Step | Question |\n|------|----------|"
    result = strip_preamble(text)
    assert result.startswith("| Step |")


def test_strip_preamble_returns_original_if_no_markdown():
    text = "No markdown here at all"
    assert strip_preamble(text) == text


# --- check_report_structure ---

def test_check_structure_full_report(sample_plan_reflect_report):
    result = check_report_structure(sample_plan_reflect_report)
    assert result["has_plan"] is True
    assert result["has_reflection"] is True
    assert result["has_meta"] is True
    assert result["correction_triggered"] is False


def test_check_structure_with_correction(sample_plan_reflect_with_correction):
    result = check_report_structure(sample_plan_reflect_with_correction)
    assert result["has_plan"] is True
    assert result["has_reflection"] is True
    assert result["has_meta"] is True
    assert result["correction_triggered"] is True


def test_check_structure_basic_report(sample_basic_report):
    result = check_report_structure(sample_basic_report)
    assert result["has_plan"] is False
    assert result["has_reflection"] is False
    assert result["has_meta"] is False
    assert result["correction_triggered"] is False


def test_check_structure_empty():
    result = check_report_structure("")
    assert result["has_plan"] is False
    assert result["has_meta"] is False


# --- constants ---

def test_default_model_is_set():
    assert "claude" in DEFAULT_MODEL


def test_default_tools_contain_websearch():
    assert "WebSearch" in DEFAULT_TOOLS
    assert "WebFetch" in DEFAULT_TOOLS


def test_default_permission_mode():
    assert DEFAULT_PERMISSION_MODE == "bypassPermissions"
