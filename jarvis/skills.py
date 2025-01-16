from jarvis.utilities import warn_msg, error_msg, congratz, clean, rawText, getResource, requireResources
from jarvis.memory import recordAction
import jarvis.custom_modules as jarvis_modules
from jarvis.custom_modules import llm, browser, gmail, iot

from AppOpener import open as app_open, close as app_close

from bs4 import BeautifulSoup as bs
from datetime import datetime
import json
import os
import schedule
import subprocess
import threading
import time
import unicodedata
import urllib.request
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Class to encapsulate various skills
class skills():   
    #Initialization
    def __init__ (self, intel, memory_manager):
        self.intel = intel
        self.memory_manager = memory_manager
        self.getAllResources()
        self.iAttemptCreateBrowser = 0
        
        #Routine scheduling
        schedule.every(self.intel['mailCheckIntervalMinutes']).minutes.do(self.rf_gmailAutomate)
        schedule.every(self.intel['refreshIOTIntervalMinutes']).minutes.do(self.rf_refreshIOTDevices)
        self.rf_runPending()
 
    def getAllResources(self):
        # Find all custom modules and initiate them all
        self.resources = []
        clsMembers, thList = [], []
        for attr in dir(jarvis_modules):
            if attr.startswith('__'): continue

            var = getattr(jarvis_modules, attr)
            for attr2 in dir(var):
                var2 = getattr(var,attr2)
                try:
                    if var2.isCustomJarvisModule:
                        clsMembers.append(var2)
                        thList.append(threading.Thread(target = self.thInitModule,  args = (var2, ) ))
                        time.sleep(0.05)
                        thList[-1].start()
                except:
                    pass
        self.clsMembers = clsMembers      
        
    def thInitModule(self, obj):
        self.resources.append(obj(self.intel, self.resources, self.memory_manager))
        print ('Thread initModule {} complete.'.format(obj))
    
    def terminate(self):
        print('Terminating all module.')
        try:
            self.memory_manager.terminate()   
            getResource(self.resources, 'browser').terminate()
            getResource(self.resources, 'iot').terminate()
        except:
            pass
        
    def getAllSkillFunctions(self):
        return [x for x in dir(self) if x[0:3]=='sf_']

################################################################
###  Routine Functions
################################################################
    def rf_runPending(self):
        schedule.run_pending()
    
    @requireResources(['gmail'])
    def rf_gmailAutomate(self):
        getResource(self.resources,'gmail').gmailAutomate()

    @requireResources(['iot'])
    def rf_refreshIOTDevices(self):
        getResource(self.resources,'iot').refreshActive()               
           
################################################################
###  Skill Functions
###  Format: stat_code, msg = func(self, bReturnTags, argList)
### bReturnTags = ([action nature],[other identifiers])
################################################################
    
    @recordAction('sf')
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
    
    
    @recordAction('sf')
    @requireResources(['gmail'])
    def sf_automateMailBox(self,bReturnTags,argList=None):
        if bReturnTags:
            return (['others'], ['automate', 'mailbox', 'email', 'gmail'], 
                    'automate the mailbox, function argument is an empty list. ')    
        
        try:
            getResource(self.resources,'gmail').gmailAutomate()
            return 0, 'Automation started in background.'
        except Exception as e:
            return -2, 'Sorry operation failed: {}'.format(str(e))
        
    @requireResources(['browser'])                    
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

    @recordAction('sf')            
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
    @recordAction('sf')
    @requireResources(['browser'])  
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

    @recordAction('sf')
    @requireResources(['browser'])  
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

        
    @recordAction('sf')    
    @requireResources(['browser'])  
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
        
    @recordAction('sf')
    @requireResources(['browser'])  
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
        
    @recordAction('sf')    
    def sf_suspendComputer(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['others'], ['sleep', 'hibernate', 'off'], 'suspend or hibernate or put computer to sleep, function argument is an empty list. ')
        
        try:            
            bExistShutDownUtility = os.path.exists(self.intel['pathShutDownUtility'])
            if bExistShutDownUtility:
                print('Suspending computer.')
                self.memory_manager.terminate()
                t1 = threading.Thread(target = self.thSuspend, args=(self.intel['pathShutDownUtility'],))
                t1.start()
                return 0, ''
            else:
                error_msg('Unable to suspend computer - Shut down utility not found.')
                return -1, 'Sorry, no utility to suspend computer.'
        except Exception as e:
            error_msg ('Exception occured while suspending computer. {}'.format(e))
            return -2, 'Sorry, operation failed: {}'.format(e)
    
    def thSuspend(self, pathShutDownUtility):
        time.sleep(5)            
        subprocess.call([pathShutDownUtility, '-d', '-t', '0'])
    
    @recordAction('sf')
    def sf_tellDateTime(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['inform'], ['date', 'time'], 'informs the date and time now, function argument is an empty list. ')
        
        try:
            sToday = datetime.now().strftime("%I %M %p %A %d %B")
            congratz ('Time now: {}'.format(sToday))
            return 0, 'The time now is {}.'.format(sToday)
        except Exception as e:
            return -2, 'Sorry, operation failed: {}'.format(e)
        
    @recordAction('sf')        
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
        
    @recordAction('sf')    
    def sf_closeApp(self, bReturnTags,argList=None):
        if bReturnTags:
            return (['close'],[], 'closes an application in the computer, argument is the application name. ')
        
        app_name = argList[0]
        try:
            app_close(app_name, match_closest=True, throw_error=True)  
            return 0, 'Closing {}.'.format(app_name)
        except Exception as e:
            return -2, 'Sorry, operation failed: {}.'.format(e)
 
    @requireResources(['iot','llm'])
    def sf_ctrlIotDevices(self, bReturnTags,argList):
        cIoT = getResource(self.resources, 'iot')
        if bReturnTags:
            return (['control'],['iot', 'devices'], cIoT.explainDevices())

        resp = argList[0]
        print('got argument {}'.format(resp))
        # Check response type
        try:
            respJSON = json.loads(resp.replace('\'','"'))
            print('reached reading JSON: {}'.format(respJSON))
            if ('id' not in respJSON) or ('control' not in respJSON):
                error_msg('Invalid JSON format, got {}'.format(respJSON))
                return -1, 'Invalid JSON format, got {}'.format(respJSON)
        except Exception as e:
            error_msg ('Error in JSON-ify resp, got resp {} \n Error: {}'.format(resp, e))
            return -1, 'Error in JSON-ify resp, got resp {} \n Error: {}'.format(resp, e)

        try:
            deviceid, control = respJSON['id'],respJSON['control'] 
            print ('[IOT] Controlling {} with value {}'.format(deviceid, control))
            cIoT.ctrlDeviceByID(deviceid, control)            
            return 0, 'Controlling device.'
        except Exception as e:
            raise
            return -2, 'Sorry, operation failed: {}.'.format(e)    