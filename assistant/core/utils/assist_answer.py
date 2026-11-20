
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types


ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_PATH)

UNCLEAR = "НЕЯСНО:"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """
Ти голосовий помічник користувача.

Твоє завдання допомагати з повсякденними питаннями,
пояснювати складні речі простими словами та давати корисні відповіді.

Правила спілкування:
- Відповідай мовою користувача.
- Говори природно та простими словами.
- Не використовуй складні формулювання без потреби.
- Відповідай коротко та по суті.
- Зазвичай використовуй від 1 до 3 коротких речень.
- Не використовуй Markdown, списки або заголовки.
- Не повторюй запит користувача у відповіді.
- Не починай відповідь із зайвих привітань.
- Якщо питання просте, одразу відповідай на нього.
- Якщо користувач просить щось пояснити,
  пояснюй так, щоб це було легко зрозуміти.
- Не вигадуй факти.
- Якщо не впевнена у відповіді, чесно скажи про це.
- Не додавай зайвих подробиць без потреби.

Робота з часом:
- Використовуй переданий контекст часу комп'ютера.
- Враховуй дату, день тижня та часовий пояс.
- Правильно розумій слова сьогодні, завтра, вчора,
  вранці, ввечері та інші вказівки щодо часу.
- Якщо користувач запитує поточний час,
  використовуй передані дані, а не намагайся його вгадати.
- Під час обчислення часу враховуй місцевий часовий пояс.

Ти голосовий помічник.
Твої відповіді мають звучати природно під час озвучування.
"""

_client = None


def get_time_context() -> str:
    now = datetime.now().astimezone()

    return (
        f"Дата: {now.strftime('%d.%m.%Y')}\n"
        f"День недели: {now.strftime('%A')}\n"
        f"Время: {now.strftime('%H:%M:%S')}\n"
        f"Часовой пояс: {now.tzname()}\n"
        f"Смещение UTC: {now.strftime('%z')}"
    )


def get_client():
    global _client

    if not API_KEY:
        raise RuntimeError("Не задан GEMINI_API_KEY в .env")

    if _client is None:
        _client = genai.Client(api_key=API_KEY)

    return _client


def ans(text: str) -> str:
    text = text.strip()

    if len(text) < 3:
        return UNCLEAR

    try:
        client = get_client()

        context = get_time_context()

        response = client.models.generate_content(
            model=MODEL,
            contents=(
                f"Контекст текущего времени:\n{context}\n\n"
                f"Сообщение пользователя:\n{text}"
            ),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=120,
            ),
        )

        answer = response.text

        if not answer:
            return UNCLEAR

        return answer.strip()

    except Exception as error:
        print(f"Ошибка Gemini API: {error}", flush=True)
        raise
