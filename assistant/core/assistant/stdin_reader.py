import sys
import threading

# Службові команди від вікна (не є текстом для помічника)
MIC_OFF = "__MIC_OFF__"
MIC_ON = "__MIC_ON__"
CONTROL_COMMANDS = {MIC_OFF, MIC_ON}


class StdinReader:
    def __init__(self, on_text, is_running, on_control=None):
        self.on_text = on_text
        self.is_running = is_running
        self.on_control = on_control

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.is_running():
            line = sys.stdin.readline()
            if not line:
                break
            text = line.strip()
            if text in CONTROL_COMMANDS and self.on_control:
                self.on_control(text)
                continue
            if text:
                print(f"Текстові команди: {text}", flush=True)
                self.on_text(text)