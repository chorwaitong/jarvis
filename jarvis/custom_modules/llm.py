from ..utilities import error_msg, congratz

from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

class llm():
    moduleType = 'LLM\Gemini'
    isCustomJarvisModule = True
    
    #Initialization
    def __init__ (self, intel, resources, memory_manager):
        try:
            print ('Initializing LLM module')
            self.intel, self.resources, self.memory_manager = intel, resources, memory_manager
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