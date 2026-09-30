from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

ACTIONS: dict[str, "Action"] = {}


@dataclass
class ActionContext:
    listen: Callable[[], str | None]
    speak: Callable[[str], None]
    stop: Callable[[], None]


class Action(ABC):
    name: str

    @abstractmethod
    def execute(self, ctx: ActionContext, text: str, matched: str) -> None: ...


def register(cls):
    ACTIONS[cls.name] = cls()
    return cls