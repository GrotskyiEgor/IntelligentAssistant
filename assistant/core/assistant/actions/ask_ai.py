# from core.utils.assist_answer import UNCLEAR, ans

# from .base import Action, register

# IDLE_REPLY = "Я тут. Чим можу допомогти?"

# @register
# class AskAI(Action):
#     name = "ask_ai"

#     def execute(self, ctx, text, matched):
#         query = text.replace(matched, "", 1).strip(" ,.!?")

#         if len(query) < 3:
#             return ctx.speak(IDLE_REPLY)

#         try:
#             answer = ans(query)
#         except Exception as error:
#             print(f"Помилка ШІ: {error}", flush=True)
#             return ctx.speak("Не вдалося отримати відповідь, спробуйте пізніше")

#         if answer.startswith(UNCLEAR):
#             return ctx.speak(IDLE_REPLY)

#         ctx.speak(answer)