import datetime

from django.db import DatabaseError

from .base import Action, register
from ..nlp.dialog import ask_text
from ..nlp.text import normalize_text

WEEK_DAYS = 7  # "на тиждень" = сьогодні + наступні 6 днів

WEEKDAYS = ("Понеділок", "Вівторок", "Середа", "Четвер", "Пʼятниця", "Субота", "Неділя")


def detect_period(text):
    """Повертає 'week', 'today', 'tomorrow' або None, якщо період не названо."""
    words = normalize_text(text or "")

    if "тиж" in words:
        return "week"
    if "завтра" in words:
        return "tomorrow"
    if "сьогодні" in words or "день" in words or "денн" in words:
        return "today"
    return None


def tasks_word(count):
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} завдання"
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return f"{count} завдання"
    return f"{count} завдань"


def title_of(task):
    title = (getattr(task, "title", "") or "").strip()
    return title or f"Завдання {task.pk}"


def day_label(day, today):
    if day == today:
        return "Сьогодні"
    if day == today + datetime.timedelta(days=1):
        return "Завтра"
    return WEEKDAYS[day.weekday()]


ORDINALS = (
    "Перше", "Друге", "Третє", "Четверте", "П'яте",
    "Шосте", "Сьоме", "Восьме", "Дев'яте", "Десяте",
)


def task_line(index, task):
    """Наприклад: «Перше о 09:00. Назва» або «Завдання 11 о 14:30. Назва»."""
    ordinal = ORDINALS[index] if index < len(ORDINALS) else f"Завдання {index + 1}"
    return f"{ordinal} о {task.time:%H:%M}. {title_of(task)}"


def tasks_text(tasks):
    return ". ".join(task_line(index, task) for index, task in enumerate(tasks))


def load_tasks(first_day, last_day):
    from core.models import Task

    return list(
        Task.objects.filter(day__gte=first_day, day__lte=last_day).order_by("day", "time")
    )


@register
class Tasks(Action):
    name = "tasks"

    def execute(self, ctx, text, matched):
        period = detect_period(text)

        if period is None:
            answer = ask_text(
                ctx,
                "На сьогодні, на завтра чи на тиждень?",
                "Не почула. Скажіть: сьогодні, завтра або тиждень",
            )
            if answer is None:
                return
            period = detect_period(answer)
            if period is None:
                return ctx.speak("Не зрозуміла, який розклад потрібен")

        today = datetime.date.today()

        try:
            if period == "week":
                last = today + datetime.timedelta(days=WEEK_DAYS - 1)
                self.say_week(ctx, load_tasks(today, last), today)
            else:
                day = today if period == "today" else today + datetime.timedelta(days=1)
                self.say_day(ctx, load_tasks(day, day), day, today)
        except DatabaseError as error:
            print(f"TASKS ERROR: {error}", flush=True)
            ctx.speak("Не вдалося отримати розклад з бази")

    @staticmethod
    def say_day(ctx, tasks, day, today):
        when = "сьогодні" if day == today else "завтра"

        if not tasks:
            return ctx.speak(f"На {when} завдань немає")

        ctx.speak(f"На {when} {tasks_word(len(tasks))}. {tasks_text(tasks)}")

    @staticmethod
    def say_week(ctx, tasks, today):
        if not tasks:
            return ctx.speak("На тиждень завдань немає")

        ctx.speak(f"На тиждень {tasks_word(len(tasks))}")

        by_day = {}
        for task in tasks:
            by_day.setdefault(task.day, []).append(task)

        for day, day_tasks in by_day.items():
            ctx.speak(f"{day_label(day, today)}. {tasks_text(day_tasks)}")
