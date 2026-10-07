import os
from collections.abc import Callable

from google import genai

AnswerModel = Callable[[str], str]
GEMINI_MODEL = "gemini-3.5-flash-lite"

def ans(text: str, model: AnswerModel | None = None) -> str:
    question = text.strip()
    if not question:
        return "Напишіть запитання, і я постараюся на нього відповісти."

    if model is not None:
        answer = model(question)
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Вкажіть API-ключ у змінній оточення GEMINI_API_KEY.")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=question,
        )
        answer = response.text or ""

    return answer.strip() or "Модель не повернула відповідь. Спробуйте сформулювати запитання інакше."
