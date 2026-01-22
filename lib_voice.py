import pychromecast
from gtts import gTTS
import time
from helpers import get_local_ip


class Voice:
    def __init__(self, lang='ru'):
        chromecasts, browser = pychromecast.discover_chromecasts()
        time.sleep(5)

        print(f"Найдено устройств: {len(chromecasts)}")
        for cc in chromecasts:
            print(f"- {cc.friendly_name} at {cc.host}:{cc.port}")

        if chromecasts:
            self.cast = pychromecast.get_chromecast_from_cast_info(
                chromecasts[0],
                zconf=browser.zc
            )
            self.cast.wait()
            print(f"✓ Подключено к: {self.cast.name}")
        else:
            browser.stop_discovery()

        self.lang = lang
        self.ip = get_local_ip()

    def say(self, text, lang=None):
        lang = lang or self.lang
        tts = gTTS(text=text, lang=lang)
        tts.save("tts.mp3")
        self.cast.media_controller.play_media(f'http://{self.ip}:8000/tts.mp3', 'audio/mp3')


if __name__ == '__main__':
    voice = Voice()
    text = "Привет, это тест"
    voice.say(text)

    text = "Следующий автобус через 12 минут"
    voice.say(text)
