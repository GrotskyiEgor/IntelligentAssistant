from django.core.management.base import BaseCommand
 
from core.assistant.services.app_scanner import mark_scanned, save_apps, scan_apps
 
 
class Command(BaseCommand):
    help = "Шукає встановлені програми і додає їх у AppCommand"
 
    def add_arguments(self, parser):
        parser.add_argument("--deep", action="store_true",
                            help="Windows: додатково проглянути Program Files")
 
    def handle(self, *args, **options):
        found = scan_apps(deep=options["deep"])
        if found is None:
            self.stderr.write("Підтримуються лише Windows і macOS")
            return
 
        added = save_apps(found)
        mark_scanned()
        self.stdout.write(f"Знайдено: {len(found)}, додано нових: {added}")
 