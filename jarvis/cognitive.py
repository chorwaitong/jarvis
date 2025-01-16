from jarvis.memory import recordAction
import jarvis.skills as skills
from jarvis.utilities import warn_msg, error_msg, congratz, getResource, requireResources
import threading
import time

class cognitive():    
    """
    This class handles the cognitive aspects of Jarvis,
    including understanding user input and interacting with skills.
    """

    def __init__ (self,intel, memory_manager):
        """
        Initialize the cognitive class with Intel configuration and memory manager.
        Args:
          intel (dict): A dictionary containing Jarvis configuration information.
          memory_manager (jarvis.memory.JarvisMemoryManager): An object for managing Jarvis's memory.
        """
        self.state = 0
        self.intel = intel
        self.memory_manager = memory_manager
        self.skills = skills.skills(intel, memory_manager)
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
    
    @recordAction('command')
    @requireResources(['llm'])
    def commandComprehendLangChain (self, wordlist):
        #     Comprehend user's command using Large Language Model (LLM) if available,       
        self.stateUpdate(2)
        try:            
            print('Checking memory for identical command')
            idxMemMatch  = self.memory_manager.memory[(self.memory_manager.memory.action_type == 'command') 
                                                           & ([wordlist == x if isinstance(x,list) else False for x in self.memory_manager.memory.args.map(lambda x:x[0])])].index
            if len(idxMemMatch)>0:
                congratz('Matched command found')
                return self.memory_manager.memory.loc[idxMemMatch[-1]].result
            
            print("No memory match, using LLM to understand command....")
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
            raise
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