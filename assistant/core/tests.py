from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Task
from .tasks import create_task


class TaskTests(TestCase):
    def setUp(self):
        self.data = {
            "title": "Звіт",
            "description": "Підготувати звіт",
            "day": date(2026, 11, 28),
            "time": time(17, 30),
            "difficulty": 2,
            "photos": ["photos/report.png"],
        }

    def test_creates_task_from_dictionary(self):
        task = create_task(self.data)
        saved = Task.objects.get(pk=task.pk)

        for field, value in self.data.items():
            self.assertEqual(getattr(saved, field), value)
        self.assertIsNotNone(saved.createdAt)
        self.assertIsNotNone(saved.updatedAt)

    def test_rejects_invalid_task(self):
        with self.assertRaises(ValidationError):
            create_task({**self.data, "title": " "})
        with self.assertRaises(ValidationError):
            create_task({**self.data, "photos": "report.png"})

        self.assertFalse(Task.objects.exists())
