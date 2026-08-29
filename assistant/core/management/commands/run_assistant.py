from django.core.management.base import BaseCommand
import speech_recognition, platform, os, subprocess, webbrowser, pyautogui, pygame


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if kwargs.get("command") == "help":
            self.help()
            return

        print('Hello')

    def add_arguments(self, parser):

        parser.add_argument(
            "command",
            nargs="*",
            type=str
        )

    def help(self):
        print("assistant help")