import pyttsx3
import threading
import time

class utterance():
    def __init__(self):    
        global bIsUttering, bShouldUtter, voice_engine, inSilencing
        bIsUttering = False
        bShouldUtter = True
        voice_engine = pyttsx3.init()
        voice_engine.setProperty('rate', 150)  # Setting up new voice rate
        voice_engine.setProperty('volume', 1.0)  # Setting up volume level  between 0 and 1
        voice_engine.setProperty('voice', voice_engine.getProperty('voices')[1].id) #You can choose the voice ID, depending on your computer.

    def say (self, text):
        global bShouldUtter
        bShouldUtter = True
        t1 = threading.Thread(target = self.thTalk, args = (text, ) )
        t1.start()
    
    
    def thTalk (self, text): 
        global bShouldUtter, isSilencing, voice_engine
        if voice_engine._inLoop:
            voice_engine.endLoop()
            time.sleep(1)
        if not voice_engine._inLoop:
            voice_engine.startLoop(False)
            time.sleep(0.5)
        
        try:
            voice_engine.say(text)   
            time.sleep(0.5)
            voice_engine.iterate()
        except:
            pass
        
        return True
           
    def terminate (self):
        try:
            self.stop()
            self.voice_engine.endLoop()      
            self.voice_engine = None
        except:
            pass
