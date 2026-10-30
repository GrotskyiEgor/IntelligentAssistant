import re
 
from .base import Action, register
from ...utils.assist_answer import ans
 
# Просимо коротку відповідь без розмітки, бо її буде озвучувати TTS
PROMPT = (
    "Відповідай українською, коротко (2-3 речення), простими словами, "
    "без markdown, списків і емодзі. Питання: {question}"
)
MAX_CHARS = 700
 
 
def clean_for_speech(text) :
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[*_`#>]+", "", text)
    text = " ".join(text.split())  # один рядок, щоб GUI не губив продовження
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        text = cut[: cut.rfind(" ")] + "..."
    return text
 
 
@register
class Ask(Action):
    name = "ask"
 
    def execute(self, ctx, text, matched):
        question = text.replace(matched, "", 1).strip(" ,.!?-—")
 
        if not question:
            ctx.speak("Слухаю")
            question = ctx.listen()
            if not question:
                return ctx.speak("Не почула запитання")
 
        ctx.show("Думаю...")
        try:
            answer = ans(PROMPT.format(question=question))
        except Exception as error:
            print(f"ASK ERROR: {error}", flush=True)
            return ctx.speak("Немає зв'язку з ШІ")
 
        ctx.speak(clean_for_speech(answer))