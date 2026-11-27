from pathlib import Path
from requests import Session, RequestException
from os import path, makedirs, remove

import sounddevice as sd, soundfile as sf, re


class Prevo:
    def __init__(self, api_key, save_dir='.'):
        """
        Client for the PrevoTTS text-to-speech API.

        Args:
        api_key (str): API authentication key.
        dir (str): Path where the generated audio will be saved if voice(stream=False).
        """

        self.key = api_key
        self.dir = Path(save_dir)
        self.session = Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })


    def voice(self, text, voice_type="aya", stream=False, samplerate=31500, channels=1, temp=True):
        """
        Generate speech from text using the selected voice.

        Args:
        text (str): Text to speech.
        voice_type (str): Voice type: "aya" or "alex".
        stream (bool): Play audio in real time if True, otherwise save it to a file.
        """

        try:
            with self.session.post(
                "https://prevotts.pythonanywhere.com/tts/",
                json={
                    "voice": voice_type,
                    "text": text,
                    "stream": stream,
                },
                stream=stream,
                timeout=60
            ) as response:
                text = re.sub(r"\s+", " ", re.sub(r"[!?.,;:]+", "", text.lower())).strip()

                if not response.ok:
                    raise RuntimeError(f"[API error: {response.status_code}]: {response.text}")

                if stream:
                    frame_size = channels * 2
                    pending = b""

                    with sd.RawOutputStream(
                        samplerate=samplerate,
                        channels=channels,
                        dtype="int16"
                    ) as output:
                        for chunk in response.iter_content(chunk_size=4096):
                            if not chunk:
                                continue

                            data = pending + chunk
                            aligned_size = len(data) - len(data) % frame_size

                            if aligned_size:
                                output.write(data[:aligned_size])

                            pending = data[aligned_size:]

                        if pending:
                            raise ValueError("Incomplete PCM audio frame")

                    return None

                makedirs(self.dir, exist_ok=True)
                file_path = self.dir / f"{text}.mp3"

                if not file_path.exists():
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)

                audio, samplerate = sf.read(file_path, dtype="float32")

                sd.play(audio, samplerate)
                sd.wait()

                if temp:
                    remove(file_path)

                return str(file_path)

        except RequestException as error:
            raise RuntimeError("TTS API request failed") from error

    def close(self):
        self.session.close()