import sys
import threading


class StdinReader:
    def __init__(self, on_text, is_running):
        self.on_text = on_text
        self.is_running = is_running

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.is_running():
            line = sys.stdin.readline()
            if not line:
                break
            text = line.strip()
            if text:
                print(f"Текстові команди: {text}", flush=True)
                self.on_text(text)