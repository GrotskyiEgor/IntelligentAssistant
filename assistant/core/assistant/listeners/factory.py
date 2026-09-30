from torch import cuda


def create_listener(is_running):
    if cuda.is_available():
        from .whisper import WhisperListener
        return WhisperListener(is_running)
    from .google import GoogleListener
    return GoogleListener()