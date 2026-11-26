from django.core.exceptions import ValidationError

from .models import Task


def create_task(data):
    task = Task(
        title=data["title"].strip(),
        description=data["description"],
        day=data["day"],
        time=data["time"],
        difficulty=data["difficulty"],
        photos=data["photos"],
    )
    if not isinstance(task.photos, list) or any(
        not isinstance(photo, str) or not photo.strip() for photo in task.photos
    ):
        raise ValidationError({"photos": "Вкажіть список шляхів до фото."})

    task.full_clean()
    task.save()
    return task
