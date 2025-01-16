#%% Definitions
"""
Main file for the minified Jarvis application.
"""
import pathlib
pathWorkFolder = str(pathlib.Path().absolute())+'\\'
print ('Workfolder: {}'.format(pathWorkFolder))
from jarvis.utilities import warn_msg, error_msg, congratz, getResource
from flask_socketio import SocketIO
from flask import Flask,render_template
import json
import itertools
import sys
import threading
import time

spinner = itertools.cycle(['-', '/', '|', '\\'])

intel = {}
intel['urlMail'] = 'https://mail.google.com/mail/u/'
intel['urlNews'] = 'https://news.google.com/news/rss'
intel['urlMusic'] = 'https://music.youtube.com/'
intel['urlMap'] = 'https://maps.google.com/'
intel['urlCalendar'] = 'https://calendar.google.com/'
intel['flaskUrl'] = '127.0.0.1'
intel['flaskPort'] = '5888'
intel['mqtt_broker'] = # The Broker url here, e.g., 'xxx.s1.eu.hivemq.cloud'
intel['mqtt_port'] = 8883
intel['pathWorkFolder'] = pathWorkFolder
intel['pathFFmpeg'] = pathWorkFolder + 'tools\\ffmpeg\\bin\\ffmpeg.exe'
intel['pathMemory'] = pathWorkFolder+"jarvis_memory.pkl"
intel['pathCredentials'] = pathWorkFolder+"credentials\\credentials.json" #Credentials and tokens for GMail API
intel['pathToken'] = pathWorkFolder+"credentials\\token.json"
intel['pathIOTDevices'] = pathWorkFolder+"iotDevices.xlsx"
intel['mailLoopIntervalSeconds'] = 20
intel['mailCheckIntervalMinutes'] = 30
intel['refreshIOTIntervalMinutes'] = 5
intel['maxIOTReconnectionCalls'] = 5
intel['SCOPES'] = ["https://www.googleapis.com/auth/gmail.readonly", 
                   "https://www.googleapis.com/auth/gmail.compose", 
                   "https://www.googleapis.com/auth/gmail.labels",
                   "https://www.googleapis.com/auth/gmail.modify"]
#%% Main loop   
# Initialize Jarvis components
# - Create an utterance object for speech synthesis
import jarvis.utterance as utterance
speaking = utterance.utterance()    

# - Create a memory manager object that stores selected instructions
import jarvis.memory as memory
memory_manager = memory.JarvisMemoryManager(intel) 

# - Create a cognitive object for reasoning
import jarvis.cognitive as cog
jrvs = cog.cognitive(intel, memory_manager)
   
# - Create a sensor (now incl hearing and text) object for speech recognition
import jarvis.sensory as sensory
hearing = sensory.hearing(intel)

# Uncomment below if it is desired to be always listening
hearing.startListening() 

# Flask app setup
app = Flask(__name__)
socketio = SocketIO(app)

# Route for the Jarvis app web interface
@app.route('/')
def index():
    return render_template("index.html")

# Handle Jarvis app connection established event
# Fired everytime a new web visit
@socketio.on("jarvis_app_on")
def gotJarvisAppOn(data):
    print('A Jarvis App browser is on.')
    sendIoTDevices()

# Handle user message received event
@socketio.on("user_message")
def gotUserMessage(data):
    hearing.addMessage("jarvis "+data['message'])

# Handle user action (such as device operation, on/off, etc) received event
@socketio.on("user_action")
def gotUserAction(data):
    data = json.loads(data)
    if ('module' in data) and ('value' in data):
        cIoT = getResource(jrvs.skills.resources, 'iot')
        if cIoT is None:
            error_msg ('The IOT resource object doesnt exist')
            return -1, 'The IOT resource object doesnt exist'        

        if not cIoT.isConnected():
            error_msg ('The IOT object is not connected')
            return -1, 'The IOT object is not connected'   
        
        cIoT.ctrlDeviceByID(data['module'], data['value'])  

# Handle user audio message (user utters command) received event        
@socketio.on("user_audio")
def gotAudioMessage(data):
    data = json.loads(data)
    if ('type' in data) and ('data' in data):
        if data['type']=='audio':
            print ('Received audio message')
            result = hearing.regAudio(data['data'])
            if result is not None:
                hearing.addMessage("jarvis "+result)
            
def sendMessage(sender, message):
    socketio.emit("new_message", {
        "from":sender,
        "message": message
    }) 

def sendIoTDevices():
    cIoT = getResource(jrvs.skills.resources,'iot')
    if cIoT is None:
        error_msg ('The IOT resource object doesnt exist')
        return -1, 'The IOT resource object doesnt exist'        
    
    if not cIoT.isConnected():
        error_msg ('The IOT object is not connected')
        return -1, 'The IOT object is not connected'       
    
    allIOTDevices = cIoT.getAllDevicesJSON() 
    sendMessage("iot", allIOTDevices)    

# A background thread that:
# - check and broacast the status of all IOT devices
# - check the message queue and acts if there's one
def thBackground():
    speaking.say('Good day sir.')       
    
    print ('Waiting to launch Jarvis App via browser')
    while not getResource(jrvs.skills.resources,'browser'):
        time.sleep(1)
    getResource(jrvs.skills.resources,'browser').navigate('http://{}:{}'.format(intel['flaskUrl'], intel['flaskPort']))
    
    while bBackgroundRun:
        try:               
            jrvs.skills.rf_runPending()           
                     
            # Update IOT devices
            sendIoTDevices()
            
            # Spinner in the command prompt, showing it is running
            sys.stdout.write(next(spinner))   # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char
    
            sensor_stat_code = 0
            sensor_msg = hearing.getMessage()
            if sensor_msg is None:
                time.sleep(0.5)
                continue
            
            sendMessage("user", sensor_msg)
            stat_code, msg_package = jrvs.stateTransition(sensor_stat_code, sensor_msg)
            if stat_code == 0:   
                speaking.say('Working on it.')
                if msg_package[0] == 'sf_talk':
                    speaking.say(msg_package[1])
                    sendMessage("Jarvis", msg_package[1])
                else:
                    stat_code, msg = jrvs.commandDo(msg_package[0], msg_package[1])
                    speaking.say(msg)
                    sendMessage("Jarvis", msg)
                    
            elif stat_code == 1:
                # At your service
                speaking.say(msg_package)
            elif stat_code == -10:
                pass
            elif stat_code == -11 or stat_code == -12:
                pass
                # print('Heard something, but not useful.')                
            else:
                print ('[Action stat_code {}] - {}'.format(stat_code, msg))
                speaking.say('Sorry could not comprehend.')
                
            time.sleep(0.5)
        
        except Exception as e:
            raise
            print(e)
            break
        
    speaking.terminate()
    jrvs.terminate()
    hearing.terminate()
    sys.exit(0)

# Run the background loop
bBackgroundRun = True
thBackgroundRun = threading.Thread(target = thBackground)      
thBackgroundRun.start()

socketio.run(app, host=intel['flaskUrl'], port=intel['flaskPort'],  allow_unsafe_werkzeug=True)

# Terminates
bBackgroundRun = False
sys.exit(0)  
