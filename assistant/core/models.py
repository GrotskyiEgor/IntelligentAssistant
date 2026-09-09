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
        return f"Группа додатків {self.apps.all()}"

class ChatMessage(models.Model):
    author = models.CharField(max_length=255)
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Автор - {self.author}; Текст - {self.text[:20]}"
