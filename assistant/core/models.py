from django.db import models

class VoiceAnswer(models.Model):
    request = models.CharField(max_length= 255)
    response = models.TextField()

    def __str__(self):
        return f"Відповідь на {self.request}"
    
class AppCommand(models.Model):
    path = models.CharField(max_length = 255)
    name = models.CharField(max_length= 100)
    keyword = models.CharField(max_length= 100)

    def __str__(self):
        return f"Запускає/Закриває додаток {self.name} за комнадою {self.keyword}"

class WebSite(models.Model):
    url = models.URLField(max_length = 255)
    name = models.CharField(max_length = 255)

    def __str__(self):
        return f"Відкриває сайт {self.name}"
    
class AppGroup(models.Model):
    name = models.CharField(max_length=255)
    apps = models.ManyToManyField(AppCommand)
    
    def __str__(self):
        return f"Група додатків {self.name}"

class ChatMessage(models.Model):
    author = models.CharField(max_length=255)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Автор - {self.author}; Текст - {self.text[:20]}"

# Коля

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    day = models.DateField()
    time = models.TimeField()
    difficulty = models.PositiveSmallIntegerField(choices=[
        (1, "Легка"),
        (2, "Середня"),
        (3, "Складна"),
    ])
    photos = models.JSONField(default=list, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
