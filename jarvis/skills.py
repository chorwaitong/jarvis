import base64
from bs4 import BeautifulSoup as bs
from datetime import datetime
from email import message_from_string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jarvis.templates import promptTemplateMailDraft

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import pandas as pd
import re
import requests
import subprocess
import threading
import time


# Class to encapsulate various skills
class skills():
    def __init__ (self, intel): #Initialization
        self.intel = intel
        self.gmailAuth()
        self.initLLM()
   
    def initLLM(self): #Initialize Google Gen AI   
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                max_tokens=None,
                timeout=None,
                max_retries=2,               
            )
            self.chainJSON = self.llm | JsonOutputParser()        
            if self.llm: print('LLM (LangChain) initialized.')
        except Exception as e:
            print ('Exception when initializing LLM. {}'.format(e))
        
    def gmailAuth(self):
        try:
            creds = None
            self.creds = creds
            print('Autheticating gmail.')
            if os.path.exists(self.intel['pathToken']):
                creds = Credentials.from_authorized_user_file(self.intel['pathToken'], self.intel['SCOPES'])
            
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        return -2, 'Exception when refreshing cred. {}'.format(e)
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.intel['pathCredentials'], self.intel['SCOPES']
                    )
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open(self.intel['pathToken'], "w") as token:
                    token.write(creds.to_json())
            self.creds = creds
            self.service = build('gmail', 'v1', credentials=self.creds)  
          
            print ('Obtaining gmail labels...')
            # Making sure that there are valid labels, can be customized here.
            self.validGmailLabels = False
            self.gmailLabels = self.service.users().labels().list(userId='me').execute()
            if self.gmailLabels:
                self.gmailLabels_general = [x['id'] for x in self.gmailLabels['labels'] if x['name']=='_AI_general_info'][0]
                self.gmailLabels_action = [x['id'] for x in self.gmailLabels['labels'] if x['name']=='_AI_need_action'][0]
                self.gmailLabels_urgent = [x['id'] for x in self.gmailLabels['labels'] if x['name']=='_AI_urgent'][0]
                if self.gmailLabels_general and self.gmailLabels_action and self.gmailLabels_urgent:
                    print ('Valid gmail labels obtained.')
                    self.validGmailLabels = True
                else:
                    print('One or more labels are missing, we got: ')
                    print(self.gmailLabels_general)
                    print(self.gmailLabels_action)
                    print(self.gmailLabels_urgent)
            else:
                print('Unable to obtain list of Gmail labels')
            return 0, 'GMail auth success.'
            
            
        except Exception as e:
            return -2, 'Exception occured when auth GMail, {}'.format(e)
        
    def gmailGetUnread(self): #Fetch unread emails from inbox folder
        try:
            print('Getting unread messages.')
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
            messages = results.get('messages', [])
            data = []
            if not messages:
                return 0, None
            else:
                for message in messages: #Process each unread email
                    msg = self.service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
                    msg_str = base64.urlsafe_b64decode(msg['raw'].encode("utf-8")).decode("utf-8")
                    msgID = msg['id']
                    threadID = msg['threadId']
                    internalDate = msg['internalDate']
                    mime_msg = message_from_string(msg_str)
                    subject = mime_msg['Subject']
                    sendfrom = mime_msg['From']
                    sendto = mime_msg['To']
                    sendcc  = mime_msg['Cc']
                                            
                    # Extract body
                    bodyParts = list(mime_msg.walk()) 
                        
                    data.append({'msgID':msgID, 'threadID':threadID, 'internalDate':internalDate,
                                 'sendfrom': sendfrom, 'sendto': sendto, 'sendcc': sendcc, 
                                 'subject': subject, 'bodyParts': bodyParts, 'mime_msg':mime_msg})
    
            df = pd.DataFrame(data)
            return 0, df
        except Exception as e:
            return -2, 'Exception occured when getting unread mails: {}'.format(e)  

    def gmailCreateDraft(self, threadID, sendto, sendcc, responseText='(draft)', bodyParts = []): #Draft email
        try:
            print('Drafting messages.')      
            message = MIMEMultipart('mixed')
            message.attach(MIMEText(responseText + '\n\n\n', 'plain'))
            for part in bodyParts: #Add original email content
                if part.get_content_type() == 'text/plain':
                    message.attach(MIMEText(part.get_payload(), 'plain'))
                elif  part.get_content_type() == 'text/html':
                    message.attach(MIMEText(part.get_payload(), 'html'))   
            
            message["To"] = sendto
            message["From"] = "me"
            message["Cc"] = sendcc
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            draft = {"message": {'threadId': threadID, "raw": encoded_message}}
            create_draft_response = self.service.users().drafts().create(userId='me', body=draft).execute()
            print('Draft created with response {}'.format(create_draft_response))
            return 0, create_draft_response
        except Exception as e:
            return -2, 'Exception occured when getting unread mails: {}'.format(e) 

    def gmailRelabel(self, threadID, addLabels, removeLabels=["INBOX"]): #Update mail labels.
        if not self.validGmailLabels:
            return -1, 'No valid Gmail labels, unable to proceed.'
        try:
            print('Relabelling messages.')
            result = self.service.users().threads().modify(
                userId='me',
                id=threadID,
                body={"removeLabelIds":removeLabels, "addLabelIds": addLabels}).execute()
            if result['id'] == threadID:
                return 0, 'success'
            else:        
                return -1, 'Relabelling fired but failed. {}'.format(result)
        except Exception as e:
            return -2, 'Exception occured when relabelling mails: {}'.format(e) 

    def gmailAssessAct(self,mailObj): #Analyze email content using LLM
        try:
            print('Asking LLM...')
            prompt, query = promptTemplateMailDraft()
            senddate, sendfrom, sendto, sendcc = mailObj.internalDate, mailObj.sendfrom, mailObj.sendto, mailObj.sendcc
            emailText = getTextFromEmail(mailObj.bodyParts)[0:5000]
            chain = prompt | self.chainJSON 
            outputJSON = chain.invoke({"senddate": senddate, "sendfrom": sendfrom, "sendto": sendto if sendto is not None else '' 
                                       + ' ' + sendcc if sendcc is not None else '',
                                   "email_body": emailText , "query": query})
            if 'urgent' in outputJSON and 'need_action' in outputJSON and 'draft_reply' in outputJSON:
                # outputJSON['emailText'] = emailText
                print('Urgent? {}, Need Action? {}, Reply: {}'.format(outputJSON['urgent'],outputJSON['need_action'],outputJSON['draft_reply']))
            else:
                print (outputJSON, type(outputJSON))
            return 0, outputJSON

        except Exception as e:
            return -2, 'Sorry operation failed: {}'.format(str(e))
        
def clean(text):
    trimmed = text.strip().replace("\r", "").replace("\n"," ").replace("\t", " ".replace(">>","").replace("--",""))
    trimmed = ' '.join(trimmed.split())
    return trimmed

def rawText(text):
    txtClean = clean(text)
    return re.sub(r'[^\w]', ' ', txtClean)
    return text.strip().replace("\r", "").replace("\n"," ").replace("\t", " ")

def getTextFromMailPart(part):
    if type(part) == str:
        return part
    
    contentType = part.get_content_type()
    if  contentType == 'text/plain':
        msg = part.get_payload()
    elif  contentType == 'text/html':
        msg = bs(part.get_payload(), 'html.parser').get_text()
    else:
        msg = None
    return clean(msg)

def getTextFromEmail(listMIME):
    messages = []
    for part in listMIME:
        contentType = part.get_content_type()
        if contentType == 'text/plain' or contentType == 'text/html':
            messages.append(getTextFromMailPart(part))
        elif 'multipart' in contentType:
            for part2 in part:
                if type(part2) == str:
                    continue
                else:
                    y = [getTextFromMailPart(sub_part) for sub_part in part2]      
                    for z in y:
                        if z is not None: messages.append(z) 
        else:
            continue
    output = ''
    for i in range(0, len(messages)):
        output += ' \n == Email Correspondence {} ==\n'.format(i+1)
        output += clean(messages[i])
    return output
