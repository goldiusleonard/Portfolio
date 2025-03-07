import os
import sys

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from karun import LLMConfig, SummaryGenerator


@pytest.fixture
def llm_config():
    """Test fixture for LLM configuration"""
    return LLMConfig(
        base_url="http://test.api.local",
        api_key="test-api-key",
        model="test-model",
        tone="informative",
        summary_format="paragraph",
    )


@pytest.fixture
def summary_generator(llm_config):
    """Test fixture for SummaryGenerator"""
    return SummaryGenerator(llm_config)


def test_calculate_summary_length(summary_generator):
    """Test summary length calculation for different input lengths"""
    # Very short text
    assert summary_generator._calculate_summary_length("hello world") == 2

    # Short text
    text = " ".join(["word"] * 100)  # 100 words
    assert summary_generator._calculate_summary_length(text) <= 50

    # Medium text
    text = " ".join(["word"] * 300)  # 300 words
    assert summary_generator._calculate_summary_length(text) <= 75

    # Long text
    text = " ".join(["word"] * 1000)  # 1000 words
    assert summary_generator._calculate_summary_length(text) == 100


def test_create_payload(summary_generator):
    """Test API payload creation"""
    test_text = "This is a test text."
    test_perspective = "technical"

    # Test paragraph format
    payload = summary_generator._create_payload(test_text, test_perspective)
    assert isinstance(payload, dict)
    assert "model" in payload
    assert "messages" in payload
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"

    # Test with different summary format
    summary_generator.config.summary_format = "bullets"
    payload = summary_generator._create_payload(test_text, test_perspective)
    assert "bullet points" in payload["messages"][0]["content"].lower()


@pytest.mark.asyncio
async def test_generate_summary(summary_generator):
    """Test summary generation - basic functionality"""
    test_text = "This is a test text for summary generation."
    summary = await summary_generator.generate_summary(test_text)
    assert isinstance(summary, str)


@pytest.mark.asyncio
async def test_generate_summary_empty_input(summary_generator):
    """Test summary generation with empty input"""
    summary = await summary_generator.generate_summary("")
    assert summary == "None"


@pytest.mark.asyncio
async def test_generate_summary_long_input(summary_generator):
    """Test summary generation with long input"""
    long_text = " ".join(["word"] * 1000)  # 1000 words
    summary = await summary_generator.generate_summary(long_text)
    assert isinstance(summary, str)
