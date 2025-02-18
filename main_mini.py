#%% Definitions
"""
Main file for the minified Jarvis application.
"""
import pathlib
pathWorkFolder = str(pathlib.Path().absolute())+'\\'
print ('Workfolder: {}'.format(pathWorkFolder))
from jarvis.utilities import error_msg, congratz
from AppOpener import open as app_open, close as app_close
from bs4 import BeautifulSoup as bs
from datetime import datetime
from flask_socketio import SocketIO
from flask import Flask,render_template
# import json
import itertools
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sys
import threading
import time
import urllib.request
import warnings
import webbrowser
import winreg
warnings.simplefilter(action='ignore', category=FutureWarning)

def getResource(resources, moduleName):
    if moduleName =='browser':
        module = [x for x in resources if 'browser' in str(type(x))] 
    elif moduleName =='llm':
        module = [x for x in resources if 'llm' in str(type(x))]
    else:
        return None
    
    try:
        return module[0]
    except:
        return None
    
class browser():
    """
    This class wraps the browsing capabilities.
    """
    moduleType = 'browser'
    isCustomJarvisModule = True
    
    #Initialization
    def __init__ (self, intel, resources):
        print ('Initializing own_browser module.')
        self.intel, self.resources = intel, resources
        self.hasJarvisPageOpened = False
        self.valid_browsers = []
        self.registerBrowsers()

    def isResourceReady(self):
        return True if len(self.valid_browsers)>0 else False
        
    def terminate(self):
        pass
                
    def registerBrowsers(self):
        print ('Checking registered browsers')
        listBrowsers = []
        valid_browsers = []
        try:
            trees = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]
            for tree in trees:
                try:
                    with winreg.OpenKey(tree, r"Software\Clients\StartMenuInternet", access=winreg.KEY_READ) as hkey:
                        for i in range(0,6):
                            cmd, stat = None, None
                            try:
                                subkey = winreg.EnumKey(hkey, i)
                            except: #Key didn't exist          
                                continue
                            
                            try:
                                display_name = winreg.QueryValue(hkey, subkey)
                                if not display_name or not isinstance(display_name, str):  # pragma: no cover
                                    display_name = subkey
                            except OSError:  # pragma: no cover
                                display_name = subkey
                                
                            try:
                                cmd = winreg.QueryValue(hkey, rf"{subkey}\shell\open\command")
                                cmd = cmd.strip('"')
                                stat = os.stat(cmd)
                                browser= {'name': display_name, 'path': cmd, 'stat': stat}
                                listBrowsers.append(browser)
                            except (OSError, AttributeError, TypeError, ValueError):  # pragma: no cover
                                continue
                except:
                    continue
        except FileNotFoundError as e:
            pass
        
        if len(listBrowsers)>0:
            for browser in listBrowsers:
                browser_name = browser['name'].lower()
                if 'chrome' in browser_name:
                    webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(browser['path']))
                    valid_browsers.append('chrome')
                    self.pathChrome = webbrowser.get('chrome').__dict__['name']
                elif 'edge' in browser_name:
                    webbrowser.register("edge", None, webbrowser.BackgroundBrowser(browser['path']))
                    valid_browsers.append('edge')
        self.valid_browsers = valid_browsers  
        congratz('Found {}'.format(', '.join(valid_browsers)))          
        return valid_browsers
           
    def navigate (self, url):
        try:
            webbrowser.open(url)
            return 0, 'Navigating via webbrowser'
        except Exception as e:
            return -2, str(e)
        
    def openJarvisPage(self):
        try:
            if not self.hasJarvisPageOpened:
                stat_code, msg = self.navigate('https://{}:{}'.format(self.intel['flaskLocalUrl'], self.intel['flaskPort']))
                if stat_code == 0:
                    self.hasJarvisPageOpened = True
                return stat_code, msg
            else:
                return 0,'Jarvis page has been opened'
        except Exception as e:
            return -2, str(e)        

class llm():
    """
    This class handles the LLM calls
    """
    moduleType = 'LLM\Gemini'
    isCustomJarvisModule = True
    
    #Initialization
    def __init__ (self, intel, resources):
        try:
            print ('Initializing LLM module')
            self.intel, self.resources = intel, resources
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                max_tokens=None,
                timeout=None,
                max_retries=2,               
            )
            self.chainJSON = self.llm | JsonOutputParser()        
            if self.llm: congratz('LLM (LangChain) initialized.')
        
        except Exception as e:
            error_msg ('Exception when initializing LLM. {}'.format(e))
        
    def isResourceReady(self):
        return True if self.llm else False



class cognitive():    
    """
    This class handles the cognitive aspects of Jarvis,
    including understanding user input and interacting with skills.
    """

    def __init__ (self,intel):
        """
        Initialize the cognitive class with Intel configuration and memory manager.
        Args:
          intel (dict): A dictionary containing Jarvis configuration information.
        """
        self.state = 0
        self.intel = intel
        self.skills = skills(intel)
        self.resources = None
        self.phraseWakeUp = "jarvis"
        self.getSkillsTags()
        self.countNonDetect = 0

    def terminate(self): 
        print('Terminating cognitive module.')
        self.skills.terminate()

    def stateTransition(self, sensor_stat_code, sensor_msg):
        # Handles Jarvis state transition based on sensor (hearing/message) input
        # jarvis status code
        # 0 - sleeping
        # 1 - on alert, waiting for specific input
                   
        #By here, meaning valid input has been received.    
        listSpeechOut = sensor_msg.split()
            
        if self.state == 1: 
            # If Jarvis is already on alert, process the entire message
            listSpeechOutFiltered = listSpeechOut
            
        elif self.phraseWakeUp in listSpeechOut:
            # If the wake-up phrase is detected, switch to alert state
            self.state = 1
            listSpeechOutFiltered = []
            
            # Speech/Message filtering
            idxWakeUp = max([i for i, val in enumerate(listSpeechOut) if val == self.phraseWakeUp])
            listSpeechOutFiltered = listSpeechOut[idxWakeUp+1:]
            if len(listSpeechOutFiltered) == 0:
                self.state = 1
                return 1, "At your service."
        else:
            return -11, 'wakeup phrase not found.'
        
        if self.state == 1:        
            stat_code, msg = self.commandComprehendLangChain(listSpeechOutFiltered)
            return stat_code, msg
            
        # If none of the above conditions are met, return an error
        return -12, 'end of state transition function reached unexpectedly.'
    
    def commandComprehendLangChain (self, wordlist):
        #     Comprehend user's command using Large Language Model (LLM) if available,       
        self.stateUpdate(2)
        try:            
            promptSkills = promptTemplateSkills(self.listSkillsTags)
            messages = [("system", promptSkills),
                ("human", ' '.join(wordlist)),
            ]
            cLLM = getResource(self.skills.resources, 'llm')
            ai_msg = cLLM.chainJSON.invoke(messages)
            if 'name' in ai_msg and 'argument' in ai_msg:
                congratz('Valid LLM response received. {}, type: {}'.format(ai_msg,type(ai_msg)))
                if ai_msg['name']=='sf_talk':
                    self.stateUpdate(1)
                else:
                    self.stateUpdate(0)
                return 0, (ai_msg['name'], str(ai_msg['argument']))
            else:            
                error_msg('Invalid LLM response received, got {}'.format(ai_msg))
                self.stateUpdate(0)
                return -1, 'Unexpected format returned by LLM.'
        except Exception as e:
            self.stateUpdate(0)
            return -2, 'Exception in using LangChain command analyzer, {}'.format(e)
        
    def commandDo (self, skillname, args):
        # Execute the specified skill with the given arguments.
        self.stateUpdate(2)
        print('Calling {} with args {}'.format(skillname,args ))
        stat_code, msg = getattr(self.skills,skillname)(False,[args])
        self.stateUpdate(0)
        return stat_code, msg
        
    def getSkillsTags(self):
        # Get tags for all available skills.
        # - using threading as some may takes time to load.
        try:
            allSkills = self.skills.getAllSkillFunctions()
            self.listSkillsTags, thList = [],[]
            for skill in allSkills:
                thList.append(threading.Thread(target = self.thGetSkillTag,  args = (skill, ) ))
                time.sleep(0.05)
                thList[-1].start()
        except Exception as e:
            error_msg ('Exception when populating the list of skills-tags. {}'.format(e))
            self.listSkillsTags = None
            
    def thGetSkillTag(self, skill):
        try:
            self.listSkillsTags.append((skill, getattr(self.skills,skill)(True,'')))
            self.resources = self.skills.resources
        except Exception as e:
            error_msg('Exception while getting tags for skill {}, {}'.format(skill, e))
           
    def stateUpdate (self, new_state):
        self.state = new_state


# Class to encapsulate various skills
class skills():   
    #Initialization
    def __init__ (self, intel):
        self.intel = intel
        self.getAllResources()
 
    def getAllResources(self):
        # Find all custom modules and initiate them all
        self.resources = []
        self.resources = [llm(self.intel, self.resources), browser(self.intel, self.resources)]
             
    def terminate(self):
        print('Terminating all module.')
        try:  
            getResource(self.resources, 'browser').terminate()
        except:
            pass
        
    def getAllSkillFunctions(self):
        return [x for x in dir(self) if x[0:3]=='sf_']           
           
################################################################
###  Skill Functions
###  Format: stat_code, msg = func(self, bReturnTags, argList)
### bReturnTags = ([action nature],[other identifiers])
################################################################
    
    def sf_getMailBox(self,bReturnTags,argList=None):
        if bReturnTags:
            return (['open', 'inform'], ['mail', 'mailbox','gmail', 'email'], 
                    'opens the email/gmail mailbox, function argument is an empty list. ')    
        
        urlMail = self.intel['urlMail']
        try:
            cBrowser = getResource(self.resources, 'browser')
            cBrowser.navigate(urlMail)
            return 0, 'Opening mail.'
        except Exception as e:
            return -2, 'Sorry operation failed: {}'.format(str(e))
                              
    def sf_openNewTab (self,bReturnTags,argList=[]):
        if bReturnTags:
            return (['open'], ['chrome', 'edge'], 'opens internet browser, function argument is an empty list.')                
        try:
            cBrowser = getResource(self.resources,'browser')
            urlOpen = 'https://www.google.com'
            if argList is not None:
                if len(argList)>0:
                    if 'http' in argList[0]:
                        urlOpen = argList[0]
            cBrowser.navigate(urlOpen)
            return 0, 'Opening browser.'
        except Exception as e:
            return -2, str(e)
          
    def sf_getNews(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['inform'], ['news'], 'gets the recent news, function argument is an empty list. ')            
        
        try:
            client = urllib.request.urlopen(self.intel['urlNews'])
            xml_page = client.read()
            client.close()
            soup = bs(xml_page, features="xml")
            news_list = soup.findAll("item")
            print('News List')
            print(''.join(["{:<2} - {} \n".format(i, n.title.text) for i,n in enumerate(news_list)]))
            
            text_list = ""
            for iNews in range(0,5):
                text_list += "News Number {}".format(iNews) + ': ' + news_list[iNews].title.text + ', '
            
            return 0, text_list + '.'
        except Exception as e:
            errMsg = str(e)            
            return -2, errMsg[0:min(len(errMsg),200)]
        return -1, 'something unidentifiable went wrong.' 
    
    # [Future works] The following several browser related functions seems like can be grouped into one
    def sf_webSearch(self, bReturnTags,argList):
        if bReturnTags:
            return (['inform'], [], 'perform web search, argument is the search query. ')            
        
        queryUrl = 'https://www.google.com/search?q='+argList[0]
        try:
            cBrowser = getResource(self.resources,'browser')
            cBrowser.navigate(queryUrl)
            return 0, 'Searching via browser.'
        except Exception as e:
            return -2, str(e)          

    def sf_openMusic(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['open'], ['youtube', 'music'], 'opens music or youtube muscic,function argument is an empty list. ')            
        try:
            cBrowser = getResource(self.resources,'browser')
            stat_code, msg = cBrowser.navigate(self.intel['urlMusic'])
            if stat_code == 0:                
                return 0, 'Opening music.'
            else:
                return stat_code, msg
        except Exception as e:
            return -2, 'Sorry operation failed {}'.format(str(e)[0:200])
 
    def sf_openMap(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['open'], ['direction', 'map'], 'opens the map, no function argument. ')            

        try:
            cBrowser = getResource(self.resources,'browser')
            stat_code, msg = cBrowser.navigate(self.intel['urlMap'])
            if stat_code == 0:                    
                return 0, 'Opening map.'
            else:
                return stat_code, msg
        except Exception as e:
            return -2, 'Sorry operation failed {}'.format(str(e)[0:200])
        
    def sf_openCalendar(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['open'], ['calendar','schedule'], 'opens calendar, function argument is an empty list. ')            

        try:
            cBrowser = getResource(self.resources,'browser')
            stat_code, msg = cBrowser.navigate(self.intel['urlCalendar'])
            if stat_code == 0:                    
                return 0, 'Opening calendar.'
            else:
                return stat_code, msg
        except Exception as e:
            return -2, 'Sorry operation failed {}'.format(str(e)[0:200])
        
    def sf_tellDateTime(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['inform'], ['date', 'time'], 'informs the date and time now, function argument is an empty list. ')
        
        try:
            sToday = datetime.now().strftime("%I %M %p %A %d %B")
            congratz ('Time now: {}'.format(sToday))
            return 0, 'The time now is {}.'.format(sToday)
        except Exception as e:
            return -2, 'Sorry, operation failed: {}'.format(e)
                
    def sf_openApp(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['open'],[], 'opens an application in the computer, argument is the application name. ')
        
        app_name = argList[0]
        try:
            if 'chrome' in app_name:
                self.createOwnBrowser()                
            else:
                app_open(app_name, match_closest=True, throw_error=True)  
            return 0, 'Opening {}.'.format(app_name)
        except Exception as e:
            return -2, 'Sorry, operation failed: {}.'.format(e)
        
    def sf_closeApp(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['close'],[], 'closes an application in the computer, argument is the application name. ')
        
        app_name = argList[0]
        try:
            app_close(app_name, match_closest=True, throw_error=True)  
            return 0, 'Closing {}.'.format(app_name)
        except Exception as e:
            return -2, 'Sorry, operation failed: {}.'.format(e)

def promptTemplateSkills(listSkillsTags):
    """
        Generates a prompt for the LLM based on available skills.
    """
    
    promptTemplateSkills = "You are a helpful assistant named Jarvis " \
    " that interprets instruction from me and issues command using computer language. "  \
    " The followings are the command names, purpose and the function argument: \n"
    try:
        # Catch error here as frequently the skills tags aren't in good form, 
        # due to lags (async functions) in obtaining it.
        for x in listSkillsTags:
            promptTemplateSkills += '\n ' + x[0] + ' ' + x[1][2]
            
    except Exception as e:
        error_msg('Exeption during generation of skills prompt template. Error\n {}\n\n Skill Tags: \n{}'.format(e, listSkillsTags))
        raise
        
    promptTemplateSkills += '\n\n **Instruction** \n\n Interpret the given instruction and issue to most appropriate command by ' \
            'providing the command name and the argument in JSON string. The json string should only contain two keys, i.e., ' \
            'the name and the argument, strictly NO json label in your response. '\
            'A sample of the response is {"name": "sf_webSearch", "argument": "batu caves"}. ' \
            'If there is no good match, issue a sf_talk command, and your response as the argument.'
    return promptTemplateSkills

spinner = itertools.cycle(['-', '/', '|', '\\'])

intel = {}
intel['urlNews'] = 'https://news.google.com/news/rss'
intel['urlMusic'] = 'https://music.youtube.com/'
intel['urlMap'] = 'https://maps.google.com/'
intel['urlCalendar'] = 'https://calendar.google.com/'
intel['flaskUrl'] = '127.0.0.1'
intel['flaskPort'] = '5888'
intel['pathWorkFolder'] = pathWorkFolder

#%% Main loop   
# Initialize Jarvis components
# - Create a cognitive object for reasoning
jrvs = cognitive(intel)
   
# - Create a sensor (now incl hearing and text) object for speech recognition
import jarvis.sensory as sensory
hearing = sensory.hearing(intel)

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
    sendMessage ("Jarvis", "Hi, this is a mini and all-in-one version for quick (but less comprehensive) access, the memory, IoT, Gmail, utterance are excluded.")

# Handle user message received event
@socketio.on("user_message")
def gotUserMessage(data):
    print("Got user message: {}".format(data))
    hearing.addMessage("jarvis "+data['message'])


# Handle user audio message (user utters command) received event        
@socketio.on("user_audio")
def gotAudioMessage(data):
    sendMessage ("Jarvis", "Sorry, the audio mode is turned off in this mini mode.")
            
def sendMessage(sender, message):
    socketio.emit("new_message", {
        "from":sender,
        "message": message
    }) 

# A background thread that:
# - check and broacast the status of all IOT devices
# - check the message queue and acts if there's one
def thBackground():
    print ('Waiting to launch Jarvis App via browser')
    time.sleep(2)
    getResource(jrvs.skills.resources,'browser').navigate('http://{}:{}'.format(intel['flaskUrl'], intel['flaskPort']))
    
    while bBackgroundRun:
        try:                  
                                 
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
                if msg_package[0] == 'sf_talk':
                    sendMessage("Jarvis", msg_package[1])
                else:
                    stat_code, msg = jrvs.commandDo(msg_package[0], msg_package[1])
                    sendMessage("Jarvis", msg)
                    
            elif stat_code == 1:
                sendMessage("At your service")
            elif stat_code == -10:
                pass
            elif stat_code == -11 or stat_code == -12:
                pass
                # print('Heard something, but not useful.')                
            else:
                print ('[Action stat_code {}] - {}'.format(stat_code, msg))
                
            time.sleep(0.5)
        
        except Exception as e:
            raise
            print(e)
            break
        
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
