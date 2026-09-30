from abc import ABC, abstractmethod

class Listener(ABC):
    @abstractmethod
    def listen(self) -> str | None:
        """Блокирующе слушает микрофон и возвращает распознанный текст."""