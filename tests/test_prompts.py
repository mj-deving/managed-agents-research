"""Tests for system prompt structure — validates prompts contain required elements."""

from utils import BASIC_SYSTEM_PROMPT, PLAN_REFLECT_SYSTEM_PROMPT, RESEARCHER_PROMPT


# --- BASIC_SYSTEM_PROMPT ---

def test_basic_prompt_requires_decompose():
    assert "Decompose" in BASIC_SYSTEM_PROMPT


def test_basic_prompt_requires_sources_section():
    assert "Sources" in BASIC_SYSTEM_PROMPT


def test_basic_prompt_requires_executive_summary():
    assert "Executive Summary" in BASIC_SYSTEM_PROMPT


def test_basic_prompt_forbids_fabrication():
    assert "fabricate" in BASIC_SYSTEM_PROMPT.lower() or "hallucinate" in BASIC_SYSTEM_PROMPT.lower()


# --- PLAN_REFLECT_SYSTEM_PROMPT ---

def test_plan_reflect_has_three_phases():
    assert "PHASE 1: PLAN" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "PHASE 2: EXECUTE" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "PHASE 3: REFLECT" in PLAN_REFLECT_SYSTEM_PROMPT


def test_plan_reflect_has_research_plan_table():
    assert "## Research Plan" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Research Question" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Target Source Type" in PLAN_REFLECT_SYSTEM_PROMPT


def test_plan_reflect_has_reflection_criteria():
    assert "Plan Coverage" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Source Quality" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Overall Assessment" in PLAN_REFLECT_SYSTEM_PROMPT


def test_plan_reflect_has_assessment_levels():
    assert "Strong" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Adequate" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Needs Improvement" in PLAN_REFLECT_SYSTEM_PROMPT


def test_plan_reflect_has_meta_section():
    assert "## Meta" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Research steps planned" in PLAN_REFLECT_SYSTEM_PROMPT
    assert "Reflection triggered correction" in PLAN_REFLECT_SYSTEM_PROMPT


def test_plan_reflect_limits_correction():
    assert "1-3 additional searches MAX" in PLAN_REFLECT_SYSTEM_PROMPT


# --- RESEARCHER_PROMPT ---

def test_researcher_requires_websearch():
    assert "WebSearch" in RESEARCHER_PROMPT


def test_researcher_requires_source_list():
    assert "source list" in RESEARCHER_PROMPT.lower()


def test_researcher_forbids_fabrication():
    assert "fabricate" in RESEARCHER_PROMPT.lower()


def test_researcher_word_count_guidance():
    assert "400-600 words" in RESEARCHER_PROMPT
