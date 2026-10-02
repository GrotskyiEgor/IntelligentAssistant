from torch import cuda
from .google import GoogleListener
from .whisper import WhisperListener


def create_listener(is_running):
    if cuda.is_available():
        return WhisperListener(is_running)
    
    return GoogleListener()