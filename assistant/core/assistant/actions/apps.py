import os
import webbrowser

from ..services import precesses
from .base import Action, register
from ..services.apps import find_app
from ...utils.find_path import find_path
from ..services.sites import find_site


def _target_text(text, matched):
    return text.replace(matched, "", 1).strip()

@register
class OpenApp(Action):
    name = "open"

    def execute(self, ctx, text, matched):
        target = _target_text(text, matched)
        if not target:
            ctx.speak("Не вказано, що відкрити")
            return

        app = find_app(target)
        if app:
            return self.open_app(ctx, app)

        site = find_site(target)
        if site:
            return self.open_site(ctx, site)

        ctx.speak(f"Я не знайшла ні програму, ні сайт {target}")

    def open_site(self, ctx, site):
        ctx.speak(f"Відкриваю сайт {site.name}")
        try:
            webbrowser.open(site.url)
        except Exception as error:
            print(f"Помилка відкриття сайту: {error}", flush=True)
            ctx.speak(f"Не вдалося відкрити {site.name}")

    def open_app(self, ctx, app):
        ctx.speak(f"Відкриваю {app.name}")

        if not app.path:
            ctx.speak(f"Шукаю {app.name}")
            app.path = find_path(filename=app.name)
            if not app.path:
                ctx.speak(f"Я не знайшла шлях до {app.name}")
                return
            app.save()

        try:
            precesses.open_app(app.path)
        except Exception as error:
            print(f"Помилка запуску: {error}", flush=True)