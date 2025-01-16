from ..utilities import warn_msg, error_msg, congratz, getResource
from aiohttp import ClientSession
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import base64
import json
import os
import paho.mqtt.client as mqtt
import pandas as pd
import time
from zeroconf import ServiceBrowser, Zeroconf

class iot():
    moduleType = 'iot'
    isCustomJarvisModule = True
    
    #Initialization
    def __init__ (self, intel, resources, memory_manager):
        print ('Initializing IOT..')
        self.intel, self.resources, self.memory_manager = intel, resources, memory_manager
        self.client, self.session = None, None
        if ("MQTT_USERNAME" not in os.environ) or ("MQTT_PASSWORD" not in os.environ):
            error_msg('MQTT credentials not found, unable to proceed.')            
            return None

        if not os.path.exists(self.intel['pathIOTDevices']):
            error_msg ('The file iotDevices does not exist, IOT module will not be loaded.')
            return None
               
        mqtt_username,  mqtt_password= os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"]                       
        self.devices = pd.read_excel(self.intel['pathIOTDevices'])
        self.devices['status'] = '0'
        self.devices['val'] = 0     
           
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(mqtt_username, mqtt_password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.tls_set_context()
        self.client.tls_insecure_set(False)
        self.client.connect(intel['mqtt_broker'], intel['mqtt_port'])
        self.client.loop_start()        
        self.ctrl_topics = list(self.devices.topics)
        self.subscribe_topics = []
        for cTopics in self.ctrl_topics:
            if str(cTopics) != 'nan' and len(str(cTopics))>0:
                val_topic = cTopics + "/val"
                self.subscribe_topics.append(val_topic) 
        
        if self.isConnected():
            congratz("IOT module initialized.")
    
    def isResourceReady(self):
        return self.isConnected()
    
    def terminate(self):           
        if self.client:
            print('Closing MQTT Client.')
            self.client.disconnect()
                        
    def explainDevices(self):
        devices = self.devices
        txtXplain = "Control IOT devices according to the following control types and list of devices. \n"
        txtXplain += '**Device Control:**\n * onoff: 1 or 0 for on and off\n * range: float from 0 to 1 \n\n'
        txtXplain += '**Devices:**\n'
        
        for i in range(0,len(devices)):
            txtXplain += '* {} (ID: {}, Type: {}) \n'.format(devices.loc[i,'desc'],
                                                             devices.loc[i,'id'],
                                                             devices.loc[i,'type']) 
        txtXplain += '\n The function argument is a JSON string. The json should only contain two keys, i.e., '\
                'the id and the control, do not include the json label word in the argument response.'\
                ' A sample of the function argument is {"id":"bl1", "control":1}'
                
        return txtXplain
    
    def getAllDevicesJSON (self):
        return self.devices.to_json(orient = "records")
                
    def validateControl(self, devicetype, control):
        if devicetype == 'onoff' and (control in ['0','1']):
            return True
        elif devicetype == 'range' and control>=0 and control<=1:
            return True
        else:
            return False
            
    def isConnected(self):
        return self.client.is_connected()
            
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if self.client.is_connected():
            congratz("Connection succesfull: reason code {}, fkags {}\n".format(reason_code, flags))
            self.client.subscribe("$SYS/#")
            for sTopic in self.subscribe_topics:
                self.client.subscribe(sTopic)
                time.sleep(0.1)
            self.refreshActive()                
        else:
            error_msg("Did not connect: reason code {}, flags {}\n".format(reason_code, flags))
            
    def on_message(self, client, userdata, msg):
        # print(msg.topic+" "+str(msg.payload))
        if len(msg.payload)==0 or msg.payload =="":
            return -1
                
        if '/val' in msg.topic: #This is received value type of message.
            self.updActive('topics',msg.topic, {'status':'1', 'val':msg.payload})
        
    def publish(self, topic, msg):
        result = self.client.publish(topic, msg)
        time.sleep(0.5)
        status = result.is_published()
        if status:
            # print(f"IoT - Sent `{msg}` to topic `{topic}`")
            pass
        else:
            error_msg(f"Failed to send message to topic {topic}")     
    
    def refreshActive(self):
        # This part is for MQTT devices, publish val topics, 
        # then the status will be updated in the on_message call
        self.devices['status'] = '0'
        for sTopic in self.subscribe_topics:    
            self.publish(sTopic, '')
            time.sleep(0.1)            
            
    def updActive(self, by, by_param, params):
        if by=='topics' or by=='id':
            for i in range(0,len(self.devices)):
                if self.devices.loc[i, by] in by_param:   
                   for param in params.keys():
                       self.devices.loc[i, param] = params[param]                  
                   break                 

    def ctrlDeviceByID(self, deviceID, control):
        control = str(control)
        devices = self.devices
        device = devices[devices.id == deviceID]
        if len(device)==0:
            error_msg('Got an unidentified deviceID, received {}'.format(deviceID))
            return -1, 'Unidentified ID'
        
        # Check topic value and decide control type (MQTT/ Ewelink LAN)        
        topic = str(device.topics.values[0])
        if topic != 'nan' and len(topic)>0: 
            #then this is MQTT type of control
            devicetype  = device.type.values[0]
            if not self.validateControl(devicetype, control):
                error_msg('Invalid control signal, {} is {} type but got control {} of type {}'.format(deviceID, devicetype, control, type(control)))
                return -1, 'Invalid control signal type'
            self.publish(topic, control)
        else:
            #something else, nothing for now.
            pass