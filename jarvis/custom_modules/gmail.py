from ..utilities import warn_msg, error_msg, congratz, clean, getResource
from ..memory import recordAction
import base64
from bs4 import BeautifulSoup as bs
from datetime import datetime
from email import message_from_string
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.prompts import PromptTemplate
import os
import pandas as pd
import threading
import time

class gmail():
    moduleType = 'gmail'
    isCustomJarvisModule = True
    
    #Initialization
    def __init__ (self, intel, resources, memory_manager):
        self.intel, self.resources, self.memory_manager = intel, resources, memory_manager
        stat_code, msg = self.authGmail()
        
    def isResourceReady(self):
        return True if self.creds else False
        
    def authGmail(self):
        print ('Initializing gmail module.')
        try:
            creds = None
            self.creds = creds
            self.isGmailAutomateRunning = False
            print('Autheticating gmail.')
            if os.path.exists(self.intel['pathToken']):
                creds = Credentials.from_authorized_user_file(self.intel['pathToken'], self.intel['SCOPES'])
                print('Cred file found.')
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
            print ('Building Gmail service')
            self.service = build('gmail', 'v1', credentials=self.creds)  
            
            # Making sure that there are valid labels, can be customized here.
            print ('Obtaining gmail labels...')
            self.validGmailLabels = False
            self.gmailLabels = self.service.users().labels().list(userId='me').execute()
            if self.gmailLabels:
                self.gmailLabels_general = [x['id'] for x in self.gmailLabels['labels'] if x['name']=='_AI_general_info'][0]
                self.gmailLabels_action = [x['id'] for x in self.gmailLabels['labels'] if x['name']=='_AI_need_action'][0]
                self.gmailLabels_urgent = [x['id'] for x in self.gmailLabels['labels'] if x['name']=='_AI_urgent'][0]
                if self.gmailLabels_general and self.gmailLabels_action and self.gmailLabels_urgent:
                    congratz ('Valid gmail labels obtained.')
                    self.validGmailLabels = True
                else:
                    return -1, 'The labels returned does not match with the template'
            return 0, 'GMail auth success.'
            
            
        except Exception as e:
            return -2, 'Exception occured when auth GMail, {}'.format(e)
        
    #Fetch unread emails from inbox folder
    def gmailGetUnread(self):
        try:
            if not self.service:
                return -1, 'The Gmail service object is not found, unable to proceed.'
                
            print('Getting unread messages.')
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
            messages = results.get('messages', [])
            data = []
            if not messages:
                return 0, None
            else:
                #Process each unread email
                for message in messages:
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
                                 'subject': subject, 'bodyParts': bodyParts})
    
            df = pd.DataFrame(data)
            return 0, df
        except Exception as e:
            return -2, 'Exception occured when getting unread mails: {}'.format(e)  

    def gmailRelabel(self, threadID, addLabels, removeLabels=["INBOX"]):
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

    def gmailAssessAct(self,mailObj):
        try:
            print('Asking LLM...')
            prompt, query = promptTemplateMailDraft()
            senddate, sendfrom= mailObj.internalDate, mailObj.sendfrom
            emailText = getTextFromEmail(mailObj.bodyParts)[0:5000]
            chain = prompt | self.chainJSON 
            outputJSON = chain.invoke({"senddate": senddate, "sendfrom": sendfrom, "email_body": emailText , "query": query})
            if 'urgent' in outputJSON and 'need_action' in outputJSON:
                print('Urgent? {}, Need Action? {} \n'.format(outputJSON['urgent'],outputJSON['need_action']))
            else:
                print (outputJSON, type(outputJSON))
            outputJSON['senddate'] = senddate
            outputJSON['sendfrom'] = sendfrom
            outputJSON['subject'] = mailObj.subject
            outputJSON['body'] = emailText
            return 0, outputJSON

        except Exception as e:
            return -2, 'Sorry operation failed: {}'.format(str(e))
      
    def gmailAutomate(self):
        if self.isGmailAutomateRunning:
            print ('Gmail automate is still running')
            return -1
        
        cLLM = getResource(self.resources,'llm')
        if cLLM is None:
            error_msg('LLM object is not found, cant proceed')
            return -1, 'The LLM object is not found, cant proceed'
        else:
            self.chainJSON = cLLM.chainJSON
        
        print('Starting Gmail automation thread.')
        t1 = threading.Thread(target = self.thGmailAutomate)
        t1.start()
        return 0, 'Thread Started'
        
        
    def thGmailAutomate(self):        
        print ('Automating mailbox >>>>>')
        self.isGmailAutomateRunning = True
        stat_code, email_msg = self.gmailGetUnread()
        if stat_code != 0:
            self.isGmailAutomateRunning = False
            error_msg ('Error encountered. {}'.format(email_msg))
            return -1
        
        if stat_code == 0 and email_msg is None:
            self.isGmailAutomateRunning = False
            congratz ('No unread email')
            return 0
            
        # Convert the retrieved messages into a DataFrame and sort by the internal date (most recent first)
        # , this is to avoid processing multiple messages within the same thread.
        dfUnread = email_msg.sort_values(by=['internalDate'], ascending=False)
        congratz('A total of {} records are retrieved.'.format(len(dfUnread)))
        readThreadIDs = [] # Keep track of thread IDs that have been processed
        for i in range(0, len(dfUnread)):
            lastUnread = dfUnread.loc[i]
            # Skip if the thread ID of the current email is already processed
            if lastUnread.threadID in readThreadIDs:
                print ('Assessing mail #{} - {} \n responded message, skip.'.format(i, lastUnread.subject))
                continue
            
            print('Assessing mail #{} - {}'.format(i, lastUnread.subject))
            # Analyze the email using the Language Model to assess its urgency and required action
            stat_code, outputJSON = self.gmailAssessAct(lastUnread)
            if stat_code == 0:
                if (outputJSON['urgent'].lower() == 'yes' or outputJSON['need_action'].lower() == 'yes'):                   
                    print('Assigning Action label')
                    mailLabel =[self.gmailLabels_urgent if outputJSON['urgent'].lower() == 'yes' else self.gmailLabels_action] 
                    relabel_stat_code, relabel_msg = self.gmailRelabel(lastUnread.threadID, mailLabel)
                    print ('[Code: {}] - {}'.format(relabel_stat_code, relabel_msg))                    
                else:
                    print('No action is needed, assigning general label.')
                    relabel_stat_code, relabel_msg = self.gmailRelabel(lastUnread.threadID, [self.gmailLabels_general])
                    print ('[Code: {}] - {}'.format(relabel_stat_code, relabel_msg))
                    
                readThreadIDs.append(lastUnread.threadID)
                congratz('Complete')
            else:
                error_msg('Failed to assess email. {}'.format(outputJSON))
            
            if i==len(dfUnread)-1:
                break
            else:
                time.sleep(self.intel['mailLoopIntervalSeconds'])
            
        self.isGmailAutomateRunning = False
        print ('Automation complete. \n <<<<<')

def getTextFromMailPart(part):
    if type(part) == str:
        return part
    
    contentType = part.get_content_type()
    if  contentType == 'text/plain':
        msg = part.get_payload(decode=True).decode("utf-8")
    elif  contentType == 'text/html':
        try:
            msg = bs(part.get_payload(decode=True).decode("utf-8"), 'html.parser').get_text()
        except :
            try:
                msg = bs(part.get_payload(decode=True).decode("utf-8"), 'lxml').get_text()
            except:
                msg = ''
    else:
        msg = ''
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
        
def promptTemplateMailDraft():
    prompt = PromptTemplate(
        template="Answer the user query considering the following mail correspondence. \n" \
            " Send Date: {senddate} \n Send from: {sendfrom} \n Email Body: [mail start] \n {email_body} \n [mail end] \n\n {query}\n",
        input_variables=["senddate", "sendfrom", "sendto", "sendcc", "email_body", "query"],
    )
    query = " My name is Mr Chor Wai Tong, a busy person who is normally at work and no time to attend personal emails. " \
            " Analyze the mail correspondence and act according to the following criteria: \n" \
            " ** Check if the mail requiring my action or reply (YES/NO). \n " \
            " ** Today is " 
    query += datetime.now().strftime('%b %d, %Y')
    query += " , if it requires my action within two weeks, label it as urgent (YES/NO) \n " \
            " Your response should be strictly in JSON object with two keys, i.e., 'urgent' and 'need_action'. "\
            " There should not be any json word label in your response. "\
            " An example of the response is : '''{'urgent':'YES', 'need_action':'YES'}'''"
    return prompt, query