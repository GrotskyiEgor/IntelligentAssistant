from core.models import AppCommand, AppGroup, VoiceAnswer, WebSite
from .base import Action, register


@register
class Help(Action):
    name = "help"

    def execute(self, ctx, text, matched):
        print(
            "Список можливих дій: \n\n"
            " • Додати команду \n"
            " • Видалити групу/команду/сайт \n"
            " • Закрий 'Назва додатку'\n"
            " • Відкрий 'Назва додатку'\n"
            " • Відкрий/Закрий групу 'Назва групи'\n"
            "Список додатків: ",
            flush=True,
        )
        for app in AppCommand.objects.all():
            print(f" • Ключове слово - {app.keyword}, Назва додатку - {app.name}", flush=True)

        print("\nСписок груп:", flush=True)
        for group in AppGroup.objects.all():
            apps = ", ".join(app.name for app in group.apps.all()) or "порожня"
            print(f" • {group.name}: {apps}", flush=True)

        print("\nГолосові запити:", flush=True)
        for answer in VoiceAnswer.objects.all():
            print(f" • {answer.request}", flush=True)

        print("\nСписок сайтів:", flush=True)
        for site in WebSite.objects.all():
            print(f" • {site.name}, url - {site.url}", flush=True)