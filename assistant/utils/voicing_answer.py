import edge_tts, pygame, asyncio, time, threading, os

VOICE = "uk-UA-PolinaNeural"
pygame.init()

async def create_voice(text: str, file_name: str):
    # text -> voice
    ready_voice = edge_tts.Communicate(text=text, voice=VOICE)

    # сохраняем созданый файл с звуком
    await ready_voice.save(audio_fname=file_name)

def voicing_text(text: str):
    # используя create_voice и создавая new_event_loop создаем аудио
    file_name = f"voice_temp_{time.time()}.mp3"
    
    voiceng_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(voiceng_event_loop)

    voiceng_event_loop.run_until_complete(create_voice(text=text, file_name=file_name))
    voiceng_event_loop.close()

    # если находим файл проигрываем его
    if os.path.exists(file_name):
        pygame.mixer.music.load(filename=file_name)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.2)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        # после проигрывания удаляем
        os.remove(file_name)

def run_voice(text: str):
    # новый поток для создания и проигрвывания аудио
    voicing_thead = threading.Thread(target=voicing_text, args=(text, ), daemon=True)
    voicing_thead.start()
