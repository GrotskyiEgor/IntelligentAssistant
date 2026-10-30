import os
import webbrowser

from ..services import precesses
from ..services.usage import log_app, log_site
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
            ctx.speak("Що відкрити?")
            return

        app = find_app(target)
        if app:
            return self.open_app(ctx, app, text)

        site = find_site(target)
        if site:
            return self.open_site(ctx, site, text)

        ctx.speak(f"Не знайшла {target}")

    def open_site(self, ctx, site, text):
        ctx.speak(f"Відкриваю {site.name}")
        try:
            webbrowser.open(site.url)
            log_site(site, "open", text)
        except Exception as error:
            print(f"Помилка відкриття сайту: {error}", flush=True)
            ctx.speak(f"Не вдалося відкрити {site.name}")

    def open_app(self, ctx, app, text):
        ctx.speak(f"Відкриваю {app.name}")

        if not app.path:
            ctx.speak(f"Шукаю {app.name}")
            app.path = find_path(filename=app.name)
            if not app.path:
                ctx.speak(f"Не знайшла {app.name}")
                return
            app.save()

        try:
            precesses.open_app(app.path)
            log_app(app, "open", text)
        except Exception as error:
            print(f"Помилка запуску: {error}", flush=True)


@register
class CloseApp(Action):
    name = "close"

    def execute(self, ctx, text, matched):
        target = _target_text(text, matched)
        if not target:
            ctx.speak("Що закрити?")
            return

        app = find_app(target)
        if not app:
            ctx.speak(f"Не знайшла {target}")
            return

        if not app.path:
            ctx.speak(f"Не знаю, де {app.name}")
            return

        ctx.speak(f"Закриваю {app.name}")
        closed = precesses.close_app(os.path.basename(app.path))

        if closed:
            log_app(app, "close", text)
        else:
            ctx.speak(f"{app.name} не запущена")