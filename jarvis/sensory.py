from jarvis.utilities import warn_msg, error_msg, congratz
import base64
import os
import speech_recognition as sr
import subprocess
import threading
import time

class hearing():
    def __init__(self, intel):
        self.intel = intel
        self.recognizer = sr.Recognizer()
        self.message_queue = []
        self.isListening = False

    def terminate(self):
        print('Terminating hearing module.')
        self.recognizer = None
        
    def addMessage(self,message):
        self.message_queue.append(message.lower())
    
    def getMessage(self):
        if len(self.message_queue) == 0:
            return None
        else:
            msg = self.message_queue[-1]
            self.message_queue = []
            return msg
    
    def regAudio(self, audiodata):
        audio_data = base64.b64decode(audiodata)
        pathTempFile = self.intel['pathWorkFolder'] + "temp_audio.webm"
        pathTempFileWav = self.intel['pathWorkFolder'] + "temp_audio.wav"
        print('[regAudio] Processing webm')
        with open(pathTempFile, "wb") as temp_audio_file:
            temp_audio_file.write(audio_data)
            
        print('[regAudio] Converting to wav')    
        subprocess.run([self.intel['pathFFmpeg']
                    , "-i", pathTempFile, "-ar", "16000", "-ac", "1", pathTempFileWav
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        
        print('[regAudio] Done processing')
        with sr.AudioFile(pathTempFileWav) as source:
            audio = self.recognizer.record(source)
            
        try:
            text = self.recognizer.recognize_google(audio)
            print('[regAudio] Got {}'.format(text))
            
            os.remove(pathTempFile)
            os.remove(pathTempFileWav)

            return text
        except Exception as e:
            error_msg('[regAudio] Unable to process audio file: {}'.format(e))
            try:
                os.remove(pathTempFile)
            except:
                pass
            try:
                os.remove(pathTempFileWav)  
            except:
                pass
            
            return None
    
    def startListening (self):
        print('Start listening...')
        t1 = threading.Thread(target = self.thListen) 
        t1.start()
            
    def thListen(self):   
        while True:            
            self.isListening = True
            try:
                if self.recognizer is None:
                    break
                
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source)
                
                if self.recognizer is None:
                    break
                
                command = self.recognizer.recognize_google(audio)
                self.message_queue.append(command.lower())
                terminal_size = os.get_terminal_size()
                print(f"{command:>{terminal_size.columns}}")
            
            except sr.UnknownValueError:
                # return -1, 'Cant understand audio'
                pass
            except Exception as e:
                error_msg('Recognition failed: {}'.format(e))
                break
            
            time.sleep(0.1)
        self.isListening = False
        print('Listening thread ended.')