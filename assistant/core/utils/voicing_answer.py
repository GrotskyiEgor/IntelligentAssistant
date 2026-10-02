import os
import asyncio
import tempfile
import time
import threading

import edge_tts

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame

VOICE = "uk-UA-PolinaNeural"
pygame.mixer.init()


async def create_voice(text: str, file_name: str):
    await edge_tts.Communicate(text=text, voice=VOICE).save(audio_fname=file_name)


def voicing_text(text: str):
    file_name = os.path.join(tempfile.gettempdir(), f"voice_temp_{time.time()}.mp3")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(create_voice(text=text, file_name=file_name))
    except Exception as error:
        print(f"TTS ERROR: {error}", flush=True)
        return
    finally:
        loop.close()

    if os.path.exists(file_name):
        pygame.mixer.music.load(filename=file_name)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.2)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        os.remove(file_name)


def run_voice(text: str) -> threading.Thread:
    thread = threading.Thread(target=voicing_text, args=(text,), daemon=True)
    thread.start()
    return thread