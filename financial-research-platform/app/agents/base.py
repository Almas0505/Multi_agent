"""Abstract BaseAgent that all concrete agents inherit from."""

from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger

from app.models.state import FinancialResearchState


class BaseAgent(ABC):
    """Abstract base class for all financial research agents."""

    def __init__(self, llm=None, tools: list | None = None) -> None:
        self.llm = llm
        self.tools: list = tools or []
        self.logger = logger

    @abstractmethod
    async def run(self, state: FinancialResearchState) -> dict:
        """Execute the agent logic and return a partial state update dict."""
        ...

    def _get_groq_llm(self):
        """Initialise and return a Groq LLM via langchain-groq."""
        try:
            from langchain_groq import ChatGroq  # type: ignore
            from app.config import settings

            if not settings.GROQ_API_KEY:
                logger.warning("GROQ_API_KEY not set; LLM calls will use mock responses.")
                return None

            return ChatGroq(
                model="llama3-8b-8192",
                temperature=0.1,
                groq_api_key=settings.GROQ_API_KEY,
            )
        except ImportError:
            logger.warning("langchain-groq not installed; LLM calls will use mock responses.")
            return None

    async def _invoke_llm(self, prompt: str, fallback: str = "") -> str:
        """Invoke the LLM with *prompt* and return the response text.

        Falls back to *fallback* when no LLM is configured.
        """
        if self.llm is None:
            return fallback or f"[Mock LLM response for prompt: {prompt[:80]}...]"
        try:
            from langchain_core.messages import HumanMessage  # type: ignore

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as exc:
            self.logger.warning(f"LLM invocation failed: {exc}")
            return fallback or f"[LLM unavailable: {exc}]"
