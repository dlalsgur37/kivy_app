import signal

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.popup import Popup
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen

from google.cloud import texttospeech_v1
import speech_recognition as sr
import playsound
import librosa
import numpy as np
import sounddevice as sd

from functools import partial
from plyer import vibrator
import datetime
import time
import threading
import json
import os
import sys
import math

kivy.require('2.0.0')

# Google Cloud Speech API KEY 파일 환경변수로 저장
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''# your google cloud speech API KEY File

# 기존 옵션 불러오기
with open('setting.json', 'r', encoding='utf-8') as f:
    option = json.load(f)


class DialogLabel(Label):
    pass


# 반응성을 위한 tts 기능 thread 활용
def talk_text():
    while (1):
        if os.path.isfile("speak.mp3") == True:
            playsound.playsound("speak.mp3")
            os.remove("speak.mp3")


talk = threading.Thread(target=talk_text)
talk.daemon = True


class MainScreen(Screen):
    pass


class OptionScreen(Screen):
    pass


class VoiceOptionScreen(Screen):
    pass


class NotifyOptionScreen(Screen):
    pass


class PresetOptionScreen(Screen):
    pass


class ScreenManagement(ScreenManager):
    pass


class OptionLayout(GridLayout):
    pass


class VoiceLayout(GridLayout):
    def checkbox_clicked(self, instance, value, voice):
        if value:
            option['voice']['voice_name'] = voice
            with open('./setting.json', 'w', encoding='utf-8') as make_file:
                json.dump(option, make_file, indent="\t")


class NotifyLayout(GridLayout):
    def save_called(self, layout, app):
        option['notify']['called1'] = layout.ids.nickname1.text
        option['notify']['called2'] = layout.ids.nickname2.text
        option['notify']['called3'] = layout.ids.nickname3.text
        with open('./setting.json', 'w', encoding='utf-8') as make_file:
            json.dump(option, make_file, indent="\t")

        app.root.current = 'option'


class PresetLayout(GridLayout):
    def save_preset(self, layout, app):
        option['preset']['preset1'] = layout.ids.preset1.text
        option['preset']['preset2'] = layout.ids.preset2.text
        option['preset']['preset3'] = layout.ids.preset3.text
        option['preset']['preset4'] = layout.ids.preset4.text
        option['preset']['preset5'] = layout.ids.preset5.text
        with open('./setting.json', 'w', encoding='utf-8') as make_file:
            json.dump(option, make_file, indent="\t")

        app.root.current = 'option'


class Up_bar(BoxLayout):
    switch = Switch(active=False)
    count = 1

    def switch_callback(self, switchObject, switchValue):

        if switchValue:  # switch on
            data.data.append({"text": "음성 인식이 활성화되었습니다.", "ind": 1})
            reverse_switch(switchValue)
            if self.count == 1:
                self.count = self.count + 1
                listen.start()

        else:
            data.data.append({"text": "음성 인식이 종료되었습니다.", "ind": 1})
            reverse_switch(switchValue)


def reverse_switch(state):
    global switch_state
    switch_state = state


# 반응성을 위한 stt 기능 thread 활용
def listen_sound():
    while True:
        if switch_state:
            # 음성 녹음
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)  # 소음 처리
                audio = r.listen(source)

            # 구글 음성인식을 이용한 구현
            try:
                with open('setting.json', 'r', encoding='utf-8') as f:
                    option = json.load(f)

                name_list = [option['notify']['called1'], option['notify']['called2'], option['notify']['called3']]
                now = datetime.datetime.now()
                speech_text = r.recognize_google(audio, language='ko-KR')  # 음성인식
                now_text = '[' + now.strftime('%H:%M:%S') + ']  '
                speech_text_kr = now_text + ''.join(speech_text)

                data.data.append({"text": speech_text_kr, "ind": 1})
                # 음성 분석
                for name in name_list:
                    if speech_text_kr.find('민혁') != -1:
                        data.data.append({"text": now_text + "누군가 나를 불렀습니다.", "ind": 1})
                        # vibrator.vibrate(0.5)
                        # time.sleep(0.5)
                        # vibrator.vibrate(0.5)
                        break

            except sr.UnknownValueError:
                with open('listen.wav', 'wb') as file:
                    file.write(audio.get_wav_data())

                audio_sample, sampling_rate = librosa.load('listen.wav', sr=22050)
                n_fft = 2048
                hop_length = 512

                stft = librosa.stft(audio_sample, n_fft=n_fft, hop_length=hop_length)
                spectrogram = np.abs(stft)
                log_spectrogram = librosa.amplitude_to_db(spectrogram)
                print(np.max(log_spectrogram) + 50)
                if 85 < (np.max(log_spectrogram) + 50):  # 자동차 경적과 유사하게 높은 소리
                    data.data.append({"text": now_text + "조심하세요! 큰 소리가 감지되었습니다.", "ind": 1})
                    # vibrator.vibrate(1)
                    # time.sleep(0.5)
                    # vibrator.vibrate(1)

            except sr.RequestError as e:
                data.data.append({"text": "구글 음성 인식 서비스에 접근할 수 없습니다.; {0}".format(e), "ind": 1})


listen = threading.Thread(target=listen_sound)
listen.daemon = True


class DialogList(RecycleView):
    def __init__(self, **kwargs):
        super(DialogList, self).__init__(**kwargs)
        global data
        data = self


class Under_bar(BoxLayout):
    pass


class AboutPop(Popup):
    about_count = 0
    about = {0: ('./source/guide0.png', '사진을 클릭하시면 다음 설명으로 넘어갑니다.'),
             1: ('./source/guide1.png', '옵션 버튼을 누르시면 각종 설정을 하실 수 있습니다.'),
             2: ('./source/guide2.png', '스위치를 on으로 설정하시면 주변 소리를 읽기 시작합니다.'),
             3: ('./source/guide3.png', '설정한 대화 프리셋을 통해 텍스트를 빠르게 적을 수 있습니다.'),
             4: ('./source/guide4.png', '글자를 적고 말하기 버튼을 누르시면 AI음성이 대신 읽어줍니다.')}

    def next_image(self):
        self.about_count = self.about_count + 1
        if self.about_count >= 5:
            self.about_count = 1
        about_tuple = self.about[self.about_count]
        self.ids.image.source = about_tuple[0]
        self.ids.guide.text = about_tuple[1]


class PresetPop(Popup):
    def __init__(self, **kwargs):
        super(PresetPop, self).__init__(**kwargs)
        self.ids.preset1.text = option['preset']['preset1']
        self.ids.preset2.text = option['preset']['preset2']
        self.ids.preset3.text = option['preset']['preset3']
        self.ids.preset4.text = option['preset']['preset4']
        self.ids.preset5.text = option['preset']['preset5']


class MainApp(App):
    Window.size = (500, 850)
    talk.start()

    def show_keyboard(self, root, event):
        root.focus = True

    def talkButton_clicked(self, root):
        with open('setting.json', 'r', encoding='utf-8') as f:
            option = json.load(f)

        if not (root.ids.textinput.text == ''):
            client = texttospeech_v1.TextToSpeechClient()
            synthesis_input = texttospeech_v1.SynthesisInput(text=root.ids.textinput.text)
            voice = texttospeech_v1.VoiceSelectionParams(
                name=option['voice']['voice_name'],
                language_code=option['voice']['language_code']
            )
            audio_config = texttospeech_v1.AudioConfig(
                audio_encoding=texttospeech_v1.AudioEncoding.MP3
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            with open("speak.mp3", "wb") as out:
                out.write(response.audio_content)

            root.ids.textinput.text = ''
            Clock.schedule_once(partial(self.show_keyboard, root.ids.textinput), 1)

    def saveid(self, root):
        global textinput_id
        textinput_id = root.ids.textinput
        prepop = PresetPop()
        prepop.open()

    def presetButton_clicked(self, root, num):
        if num == 1:
            textinput_id.text = root.ids.preset1.text
        elif num == 2:
            textinput_id.text = root.ids.preset2.text
        elif num == 3:
            textinput_id.text = root.ids.preset3.text
        elif num == 4:
            textinput_id.text = root.ids.preset4.text
        elif num == 5:
            textinput_id.text = root.ids.preset5.text

        Clock.schedule_once(partial(self.show_keyboard, textinput_id), 1)
        root.dismiss()


if __name__ == '__main__':
    MainApp().run()
