import logging
from functools import cache
from typing import Literal, TypeVar

import anthropic
from pydantic import BaseModel

from soltura.config import settings

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)
Effort = Literal["low", "medium", "high"]

# "default" lets the API pick a fallback model by refusal category, so a declined
# request is retried on another model inside the same call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMUnavailableError(Exception):
    pass


class LLMNotConfiguredError(LLMUnavailableError):
    pass


class LLMClient:
    # A client without a key still exists, so routes that never reach the model
    # (validation errors, saving a word) work, and the missing key surfaces only
    # when a call is actually made.
    def __init__(self, client: anthropic.AsyncAnthropic | None, model: str) -> None:
        self._client = client
        self._model = model

    async def __call__(
        self,
        schema: type[SchemaT],
        system: str,
        prompt: str,
        effort: Effort,
        max_tokens: int = 16_000,
    ) -> SchemaT:
        if self._client is None:
            raise LLMNotConfiguredError("ANTHROPIC_API_KEY is not set")
        try:
            response = await self._client.beta.messages.parse(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
                output_config={"effort": effort},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.APIConnectionError as error:
            raise LLMUnavailableError("Claude could not be reached") from error
        except anthropic.APIStatusError as error:
            logger.error(f"Claude request failed with {error.status_code}: {error.message}")
            raise LLMUnavailableError(f"Claude returned {error.status_code}") from error

        if response.stop_reason == "refusal":
            raise LLMUnavailableError("Claude declined the request")
        if response.parsed_output is None:
            raise LLMUnavailableError(f"Claude returned no answer ({response.stop_reason})")
        return response.parsed_output


@cache
def get_llm() -> LLMClient:
    api_key = settings.llm.api_key
    client = anthropic.AsyncAnthropic(api_key=api_key.get_secret_value()) if api_key else None
    return LLMClient(client, settings.llm.model)
