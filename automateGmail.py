import pathlib
pathWorkFolder = str(pathlib.Path().absolute())+'\\'
print ('Workfolder: {}'.format(pathWorkFolder))

import json
import pandas as pd
import os
import time

intel = {}
intel['pathWorkFolder'] = pathWorkFolder
intel['pathCredentials'] = pathWorkFolder+"\\credentials\\credentials.json"
intel['pathToken'] = pathWorkFolder+"\\credentials\\token.json"
intel['SCOPES'] = ["https://www.googleapis.com/auth/gmail.readonly", 
                   "https://www.googleapis.com/auth/gmail.compose", 
                   "https://www.googleapis.com/auth/gmail.labels",
                   "https://www.googleapis.com/auth/gmail.modify"]

import jarvis.skills as sk
skill = sk.skills(intel)

# Retrieve unread emails
stat_code, email_msg = skill.gmailGetUnread()

# Check if the emails were successfully retrieved
if stat_code == 0 and email_msg is not None:
    # Convert the retrieved messages into a DataFrame and sort by the internal date (most recent first)
    # , this is to avoid processing multiple messages within the same thread.
    dfUnread = email_msg.sort_values(by=['internalDate'], ascending=False)
    print('A total of {} records are retrieved.'.format(len(dfUnread)))
    
    readThreadIDs = []  # Keep track of thread IDs that have been processed
    
    # Iterate through the list of unread emails
    for i in range(0, len(dfUnread)):
        lastUnread = dfUnread.loc[i]  # Get the current unread email
        
        # Skip if the thread ID of the current email is already processed
        if lastUnread.threadID in readThreadIDs:
            print('Assessing mail #{} - {} \n Responded message, skip.'.format(i, lastUnread.subject))
            continue
        
        print('Assessing mail #{} - {}'.format(i, lastUnread.subject))
        
        # Analyze the email using the Language Model to assess its urgency and required action
        stat_code, outputJSON = skill.gmailAssessAct(lastUnread)
        
        if stat_code == 0:
            # If the email is classified as "urgent"
            if outputJSON['urgent'].lower() == 'yes':
                print('Assigning urgent label')                
                # Relabel the thread with the "urgent" label
                relabel_stat_code, relabel_msg = skill.gmailRelabel(
                    lastUnread.threadID, [skill.gmailLabels_urgent]
                )
                print('[Code: {}] - {}'.format(relabel_stat_code, relabel_msg))
            
            # If the email requires action
            elif outputJSON['need_action'].lower() == 'yes':
                print('Assigning action label')
                # Relabel the thread with the "action needed" label
                relabel_stat_code, relabel_msg = skill.gmailRelabel(
                    lastUnread.threadID, [skill.gmailLabels_action]
                )
                print('[Code: {}] - {}'.format(relabel_stat_code, relabel_msg))
            
            # If no action is needed
            else:
                print('No action is needed, assigning general label.')
                
                # Relabel the thread with the "general info" label
                relabel_stat_code, relabel_msg = skill.gmailRelabel(
                    lastUnread.threadID, [skill.gmailLabels_general]
                )
                print('[Code: {}] - {}'.format(relabel_stat_code, relabel_msg))
            
            # Mark the current thread ID as processed
            readThreadIDs.append(lastUnread.threadID)
            print('Complete')
        else:
            print('Failed to assess email. {}'.format(outputJSON))
        
        time.sleep(15)
else:
    print('Failed to obtain/ there is no unread messages. {}'.format(email_msg))  
  
print('Operation complete')
