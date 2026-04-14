"""Tests for output parsing — validates generated reports have expected structure."""

import re


def test_basic_report_has_executive_summary(sample_basic_report):
    assert "## Executive Summary" in sample_basic_report


def test_basic_report_has_key_findings(sample_basic_report):
    assert "## Key Findings" in sample_basic_report


def test_basic_report_has_sources(sample_basic_report):
    assert "## Sources" in sample_basic_report


def test_basic_report_has_conclusions(sample_basic_report):
    assert "## Conclusions" in sample_basic_report


def test_basic_report_sources_have_urls(sample_basic_report):
    sources_section = sample_basic_report.split("## Sources")[1].split("## Conclusions")[0]
    urls = re.findall(r"https?://[^\s)]+", sources_section)
    assert len(urls) >= 8


def test_plan_reflect_has_all_sections(sample_plan_reflect_report):
    assert "## Research Plan" in sample_plan_reflect_report
    assert "## Report" in sample_plan_reflect_report
    assert "## Reflection Notes" in sample_plan_reflect_report
    assert "## Meta" in sample_plan_reflect_report


def test_plan_reflect_plan_has_table(sample_plan_reflect_report):
    plan_section = sample_plan_reflect_report.split("## Report")[0]
    assert "| Step |" in plan_section
    assert "Research Question" in plan_section


def test_plan_reflect_meta_has_fields(sample_plan_reflect_report):
    meta_section = sample_plan_reflect_report.split("## Meta")[1]
    assert "Research steps planned" in meta_section
    assert "Research steps completed" in meta_section
    assert "Total web searches performed" in meta_section
    assert "Reflection triggered correction" in meta_section


def test_plan_reflect_meta_steps_match(sample_plan_reflect_report):
    meta_section = sample_plan_reflect_report.split("## Meta")[1]
    planned = re.search(r"Research steps planned\*\*:\s*(\d+)", meta_section)
    completed = re.search(r"Research steps completed\*\*:\s*(\d+)", meta_section)
    assert planned and completed
    assert planned.group(1) == completed.group(1)


def test_correction_report_meta_says_yes(sample_plan_reflect_with_correction):
    meta_section = sample_plan_reflect_with_correction.split("## Meta")[1]
    assert "Yes" in meta_section
    correction_line = [l for l in meta_section.split("\n") if "Correction details" in l][0]
    assert "N/A" not in correction_line


def test_reflection_has_overall_assessment(sample_plan_reflect_report):
    reflection = sample_plan_reflect_report.split("## Reflection Notes")[1].split("## Meta")[0]
    assert "Overall Assessment" in reflection
    assert any(level in reflection for level in ["Strong", "Adequate", "Needs Improvement"])
