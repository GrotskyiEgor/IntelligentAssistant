from .answers import is_cancel, is_no, is_yes
from .text import normalize_text

MAX_ATTEMPTS = 5


def ask_text(ctx, question: str, retry: str, attempts: int = MAX_ATTEMPTS) -> str | None:
    ctx.speak(question)

    for _ in range(attempts):
        answer = ctx.listen()

        if not answer:
            ctx.speak(retry)
            continue

        if is_cancel(answer):
            ctx.speak("Гаразд, скасовано")
            return None

        text = normalize_text(answer)
        if text:
            return text

        ctx.speak(retry)

    ctx.speak("Відповіді немає, скасовую")
    
    return None


def confirm(ctx, question: str, attempts: int = MAX_ATTEMPTS) -> bool:
    ctx.speak(question)

    for _ in range(attempts):
        answer = ctx.listen()

        if not answer:
            ctx.speak("Я не почула. Скажіть так або ні")
            continue

        if is_cancel(answer) or is_no(answer):
            ctx.speak("Гаразд, скасовано")
            return False

        if is_yes(answer):
            return True

        ctx.speak("Я не зрозуміла. Скажіть так або ні")

    ctx.speak("Відповіді немає, скасовую")

    return False