from core.models import AppCommand, VoiceAnswer, WebSite
from .base import Action, register


@register
class Help(Action):
    name = "help"

    def execute(self, ctx, text, matched):
        print(
            "Список можливих дій: \n\n"
            " • Додати команду \n"
            " • Закрий 'Назва додатку'\n"
            " • Відкрий 'Назва додатку'\n"
            " • Відкрий/Закрий групу 'Назва групи'\n"
            "Список додатків: ",
            flush=True,
        )
        for app in AppCommand.objects.all():
            print(f" • Ключове слово - {app.keyword}, Назва додатку - {app.name}", flush=True)

        print("\nГолосові запити:", flush=True)
        for answer in VoiceAnswer.objects.all():
            print(f" • {answer.request}", flush=True)

        print("\nСписок сайтів:", flush=True)
        for site in WebSite.objects.all():
            print(f" • {site.name}, url - {site.url}", flush=True)

        ctx.stop()