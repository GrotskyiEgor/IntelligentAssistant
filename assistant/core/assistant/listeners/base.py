from abc import ABC, abstractmethod

class Listener(ABC):
    @abstractmethod
    def listen(self):
        """Блокирующе слушает микрофон и возвращает распознанный текст."""