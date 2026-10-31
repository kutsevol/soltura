from typing import cast

from pydantic import BaseModel

from soltura.llm.client import Effort, LLMClient, SchemaT


class FakeLLM(LLMClient):
    # Answers each schema from its own queue, in the order the answers were given;
    # an exception in the queue is raised instead, like a failed or refused call.
    def __init__(self) -> None:
        self.responses: dict[type[BaseModel], list[BaseModel | Exception]] = {}
        self.prompts: list[str] = []

    def answer(self, *responses: BaseModel) -> None:
        for response in responses:
            self.responses.setdefault(type(response), []).append(response)

    def fail(self, schema: type[BaseModel], error: Exception) -> None:
        self.responses.setdefault(schema, []).append(error)

    async def __call__(
        self,
        schema: type[SchemaT],
        system: str,
        prompt: str,
        effort: Effort,
        max_tokens: int = 16_000,
    ) -> SchemaT:
        self.prompts.append(prompt)
        response = self.responses[schema].pop(0)
        if isinstance(response, Exception):
            raise response
        return cast(SchemaT, response)
