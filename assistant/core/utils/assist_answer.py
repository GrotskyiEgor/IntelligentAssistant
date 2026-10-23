# import os
# from collections.abc import Callable

# import anthropic

# AnswerModel = Callable[[str], str]
# CLAUDE_MODEL = "claude-haiku-5-5"
# UNCLEAR = "UNCLEAR"

# SYSTEM_PROMPT = (
#     "Ти голосовий помічник на ім'я Омі. Відповідай українською, коротко: "
#     "одне-два речення, без markdown, списків і емодзі. "
#     f"Якщо повідомлення не є зрозумілим запитанням чи проханням "
#     f"(просто звертання, уривок фрази, шум розпізнавання), відповідай рівно одним словом: {UNCLEAR}."
# )

# _client = None


# def _get_client():
#     global _client
#     if _client is None:
#         api_key = os.getenv("ANTHROPIC_API_KEY")
#         if not api_key:
#             raise RuntimeError("Вкажіть API-ключ у змінній оточення ANTHROPIC_API_KEY.")
#         _client = anthropic.Anthropic(api_key=api_key)
#     return _client


# def ans(text, model: AnswerModel | None = None):
#     question = text.strip()

#     if not question:
#         return UNCLEAR

#     if model is not None:
#         answer = model(question)
#     else:
#         response = _get_client().messages.create(
#             model=CLAUDE_MODEL,
#             max_tokens=300,
#             system=SYSTEM_PROMPT,
#             messages=[{"role": "user", "content": question}],
#         )
#         answer = "".join(block.text for block in response.content if block.type == "text")

#     answer = " ".join(answer.split())
#     return answer or UNCLEAR