from ..utilities import warn_msg, error_msg, congratz
import os
import webbrowser
import winreg

class browser():
    moduleType = 'browser'
    isCustomJarvisModule = True
    
    #Initialization
    def __init__ (self, intel, resources, memory_manager):
        print ('Initializing own_browser module.')
        self.intel, self.resources, self.memory_manager = intel, resources, memory_manager
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