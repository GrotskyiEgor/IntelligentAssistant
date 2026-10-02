from collections.abc import Callable

AnswerModel = Callable[[str], str]


def ans(text: str, model: AnswerModel | None = None) -> str:

    question = text.strip()
    if not question:
        return "Напишите вопрос, и я постараюсь на него ответить."

    if model is None:
        return "Я получил ваш вопрос, но языковая модель пока не подключена."

    answer = model(question)
    return answer.strip() or "Модель не вернула ответ. Попробуйте задать вопрос иначе."