from functools import wraps
from jarvis.utilities import warn_msg, error_msg, congratz
from datetime import datetime
import os
import pandas as pd
import pickle

class JarvisMemoryManager:
    def __init__(self, intel):
        """
        Initialize the memory manager.
            y_file (str): Path to the memory file for saving and loading data.
        """
        self.memory_file = intel['pathMemory']
        self.memory = pd.DataFrame(columns=["timestamp","action_type", "action", "args", "kwargs", "result"])  # List to store actions in memory
        self._load_memory()  # Load memory content from local file

    def _load_memory(self):
        """
        Load memory content from the local file.
        """
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'rb') as f:
                    self.memory = pickle.load(f)
                congratz(f"Memory loaded successfully from {self.memory_file}.")
            except Exception as e:
                error_msg(f"Error loading memory: {e}")
        else:
            warn_msg("No existing memory file found. Starting with an empty memory.")

    def _save_memory(self):
        try:              
            with open(self.memory_file, "wb") as f:
                pickle.dump(self.memory, f)
            congratz(f"Memory saved successfully to {self.memory_file}.")
        except Exception as e:
            error_msg(f"Error saving memory: {e}")

    def record_action(self, action_type, action, args, kwargs, result):
        # Filter out unnecessary actions
        # - excl function fired during getting skill tags
        if 'sf_' in action and args[0]:
            return True
            
        # Record an action into memory.
        action_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "action": action,
            "args": args,
            "kwargs": kwargs,
            "result": result,
        }
        self.memory = pd.concat([self.memory, pd.DataFrame([action_entry])], ignore_index=True)

    def get_memory(self):
        # Retrieve the current memory content.
        return self.memory

    def terminate(self):
        print('Terminating memory module.')
        self._save_memory()
        
        
def recordAction(action_type):
    # Decorator to record function calls to JarvisMemoryManager.
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Call the wrapped function
            result = func(self, *args, **kwargs)
            # Record the action if it is valid and successful
            if len(result) == 2:
                if result[0] == 0:
                    self.memory_manager.record_action(action_type = action_type, action=func.__name__, 
                                                      args=args,
                                                      kwargs=kwargs, result=result)
            return result
        return wrapper
    return decorator
