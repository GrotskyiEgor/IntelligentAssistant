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
    use_count = models.PositiveIntegerField(default=0)    
    last_used_at = models.DateTimeField(null=True, blank=True)

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

class CommandPhrase(models.Model):
    KIND_CHOICES = (
        ("command", "Команда"),
        ("answer", "Відповідь"),
    )
 
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="command")
    action = models.CharField(max_length=50)
    phrase = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        unique_together = ("kind", "action", "phrase")
        indexes = [models.Index(fields=["kind", "action"])]
 
    def __str__(self):
        return f"{self.kind}/{self.action}: {self.phrase}"

class AssistantState(models.Model): 
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255, blank=True)
 
    def __str__(self):
        return f"{self.key} = {self.value}"

class UsageLog(models.Model):
    KIND_CHOICES = (
        ("action", "Команда"),
        ("app", "Програма"),
    )
 
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    action = models.CharField(max_length=50)
    target = models.CharField(max_length=255, blank=True)
    app = models.ForeignKey(AppCommand, null=True, blank=True, on_delete=models.SET_NULL, related_name="usage")
    text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
 
    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.kind}/{self.action} {self.target}"

    
# Коля