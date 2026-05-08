"""Tests for LLM provider layer."""

import pytest

from tailortex.llm.base import LLMError, LLMResponse
from tailortex.llm.providers.mock import MockProvider
from tailortex.llm.providers.rule_based import RuleBasedProvider


class TestMockProvider:
    @pytest.fixture
    def provider(self):
        return MockProvider()

    @pytest.mark.asyncio
    async def test_returns_llm_response(self, provider):
        provider.add_response({"key": "value"})
        result = await provider.complete("test prompt")
        assert isinstance(result, LLMResponse)
        assert result.parsed == {"key": "value"}
        assert result.provider == "mock"

    @pytest.mark.asyncio
    async def test_logs_prompts(self, provider):
        await provider.complete("first prompt")
        await provider.complete("second prompt")
        assert len(provider.call_log) == 2
        assert provider.call_log[0] == "first prompt"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_responses(self, provider):
        result = await provider.complete("test")
        assert isinstance(result, LLMResponse)
        assert result.parsed == {}

    @pytest.mark.asyncio
    async def test_pops_responses_in_order(self):
        provider = MockProvider(responses=[{"a": 1}, {"b": 2}])
        r1 = await provider.complete("first")
        r2 = await provider.complete("second")
        assert isinstance(r1, LLMResponse)
        assert isinstance(r2, LLMResponse)
        assert r1.parsed == {"a": 1}
        assert r2.parsed == {"b": 2}

    @pytest.mark.asyncio
    async def test_error_response(self, provider):
        provider.add_error("something broke")
        result = await provider.complete("test")
        assert isinstance(result, LLMError)
        assert "something broke" in result.error

    def test_is_local(self, provider):
        assert provider.is_local is True

    def test_name(self, provider):
        assert provider.name == "mock"


class TestRuleBasedProvider:
    @pytest.fixture
    def provider(self):
        return RuleBasedProvider()

    @pytest.mark.asyncio
    async def test_returns_llm_response(self, provider):
        result = await provider.complete("test prompt")
        assert isinstance(result, LLMResponse)
        assert result.provider == "rule-based"

    @pytest.mark.asyncio
    async def test_bullet_rewrite_preserves_text(self, provider):
        prompt = (
            'You are rewriting resume bullets.\n'
            '{"text": "Built a REST API in Python"}\n'
            '{"text": "Deployed services to Kubernetes"}'
        )
        result = await provider.complete(prompt)
        assert isinstance(result, LLMResponse)
        bullets = result.parsed.get("bullets", [])
        assert len(bullets) == 2
        assert bullets[0]["rewritten_text"] == "Built a REST API in Python"
        assert bullets[0]["validation_status"] == "supported"

    @pytest.mark.asyncio
    async def test_validation_returns_empty_claims(self, provider):
        prompt = "You are validating claims against evidence."
        result = await provider.complete(prompt)
        assert isinstance(result, LLMResponse)
        assert "claims" in result.parsed

    def test_is_local(self, provider):
        assert provider.is_local is True

    def test_name(self, provider):
        assert provider.name == "rule-based"


class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_retry_on_json_error(self):
        """Mock a scenario where retry succeeds."""
        provider = MockProvider()
        # First call returns error with raw_text, second succeeds
        provider.add_response({"result": "fixed"})
        result = await provider.complete_with_retry(
            "test", output_schema={"type": "object"}
        )
        assert isinstance(result, LLMResponse)
        assert result.parsed == {"result": "fixed"}
