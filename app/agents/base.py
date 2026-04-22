from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

InputModel = TypeVar("InputModel", bound=BaseModel)
OutputModel = TypeVar("OutputModel", bound=BaseModel)


class BaseAgent(Generic[InputModel, OutputModel]):
    def run(self, payload: InputModel) -> OutputModel:
        raise NotImplementedError

