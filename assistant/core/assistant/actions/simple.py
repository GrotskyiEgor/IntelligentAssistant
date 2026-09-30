from .base import Action, register


@register
class Greeting(Action):
    name = "greeting"

    def execute(self, ctx, text, matched):
        ctx.speak("Привіт, чим можу допомогти?")


@register
class Stop(Action):
    name = "stop"

    def execute(self, ctx, text, matched):
        ctx.stop()