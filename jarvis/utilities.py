# import base64
from base64 import b64encode #, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
from functools import wraps
import hashlib
import hmac
import inspect
import json
import os
import re
import time

def warn_msg(warn_txt):
    print ('[Warning] {}'.format(warn_txt))
    
def error_msg(msg_txt):
    print ('[ERROR] {}'.format(msg_txt))
    
def congratz(msg_txt):
    print ('[/] {}'.format(msg_txt))
    
def clean(text):
    trimmed = text.strip().replace("\r", "").replace("\n"," ").replace("\t", " ".replace(">>","").replace("--",""))
    trimmed = ' '.join(trimmed.split())
    return trimmed

def rawText(text):
    txtClean = clean(text)
    return re.sub(r'[^\w]', ' ', txtClean)
    return text.strip().replace("\r", "").replace("\n"," ").replace("\t", " ")

def getResource(resources, moduleName):
    if moduleName =='browser':
        module = [x for x in resources if 'browser.browser' in str(type(x))] 
    elif moduleName =='gmail':
        module = [x for x in resources if 'gmail.gmail' in str(type(x))]
    elif moduleName =='llm':
        module = [x for x in resources if 'llm.llm' in str(type(x))]
    elif moduleName =='iot':
        module = [x for x in resources if 'iot.iot' in str(type(x))]
    else:
        return None
    
    try:
        return module[0]
    except:
        return None

def requireResources(modulelist):
    # Decorator to check for required resources before executing.
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            holdTillFound = True if 'bReturnTags' in inspect.getfullargspec(func).args else False
                
            isUnfound = True
            while isUnfound: #loop as long as it is found to be "unfound"            
                isUnfound = False #Asumme all found, and scan thru all resources
                for module_name in modulelist:
                    module = getResource(self.resources, module_name)
                    if module is None:
                        isUnfound = True
                        break
                    elif not module.isResourceReady():                        
                        isUnfound = True
                        break
                
                if isUnfound:
                    warn_msg ('Not running {} as resource {} is not reeady.'.format(func, module_name))
                    if holdTillFound:
                        time.sleep(2)
                        continue
                    else:
                        return -3, 'Insufficient Resource(s)'
                                
            # Call the wrapped function
            result = func(self, *args, **kwargs)
                        
            return result
        return wrapper
    return decorator

def sign(key, msg):
    return hmac.new(key, msg, hashlib.sha256).digest()
 
def encrypt (data: dict, devicekey: str):    
    # Convert the device key to bytes
    devicekey = devicekey.encode("utf-8")
    # Derive a key using an MD5 hash
    digest = hashes.Hash(hashes.MD5(), backend=default_backend())
    digest.update(devicekey)
    key = digest.finalize()
    # Generate a random IV
    iv = os.urandom(16)
    # Convert the plaintext to bytes
    plaintext = json.dumps(data).encode("utf-8")
    # Create a cipher object and encrypt the padded plaintext
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    # Apply PKCS7 padding
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    # Encrypt the data
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return b64encode(ciphertext).decode('utf-8'), b64encode(iv).decode("utf-8")