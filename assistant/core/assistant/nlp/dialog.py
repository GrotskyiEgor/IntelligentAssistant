from .answers import is_cancel, is_no, is_yes
from .text import normalize_text

MAX_ATTEMPTS = 5


def ask_text(ctx, question, retry, attempts = MAX_ATTEMPTS):
    ctx.speak(question)

    for _ in range(attempts):
        answer = ctx.listen()

        if not answer:
            ctx.speak(retry)
            continue

        if is_cancel(answer):
            ctx.speak("Скасовано")
            return None

        text = normalize_text(answer)
        if text:
            return text

        ctx.speak(retry)

    ctx.speak("Скасовую")
    
    return None


def confirm(ctx, question, attempts = MAX_ATTEMPTS) -> bool:
    ctx.speak(question)

    for _ in range(attempts):
        answer = ctx.listen()

        if not answer:
            ctx.speak("Так чи ні?")
            continue

        if is_cancel(answer) or is_no(answer):
            ctx.speak("Скасовано")
            return False

        if is_yes(answer):
            return True

        ctx.speak("Не зрозуміла. Так чи ні?")

    ctx.speak("Скасовую")

    return False