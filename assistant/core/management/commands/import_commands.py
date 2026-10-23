import json
 
from django.core.management.base import BaseCommand
 
from core.assistant.config import COMMANDS_JSON_PATH
from core.assistant.nlp.text import normalize_text
from core.models import CommandPhrase
 
 
class Command(BaseCommand):
    help = "Імпортує фрази з commands.json у таблицю CommandPhrase"
 
    def add_arguments(self, parser):
        parser.add_argument("--path", default=str(COMMANDS_JSON_PATH))
        parser.add_argument("--replace", action="store_true",
                            help="видалити всі існуючі фрази перед імпортом")
 
    def handle(self, *args, **options):
        with open(options["path"], "r", encoding="utf-8") as file:
            data = json.load(file)
 
        if options["replace"]:
            CommandPhrase.objects.all().delete()
 
        created = skipped = 0
        for action, value in data.items():
            if action == "answers":
                pairs = [("answer", name, phrases) for name, phrases in value.items()]
            else:
                pairs = [("command", action, value)]
 
            for kind, name, phrases in pairs:
                for phrase in phrases:
                    _, was_created = CommandPhrase.objects.get_or_create(
                        kind=kind, action=name, phrase=normalize_text(phrase)
                    )
                    created += was_created
                    skipped += not was_created
 
        self.stdout.write(f"Додано: {created}, вже було: {skipped}")