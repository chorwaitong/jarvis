from langchain_core.prompts import PromptTemplate
from datetime import datetime

def promptTemplateMailDraft():
    prompt = PromptTemplate(
        template="Answer the user query considering the following mail correspondence. \n" \
            " Send Date: {senddate} \n Send from: {sendfrom}\n Send to: {sendto} \n Email Body: [mail start] \n {email_body} \n [mail end] \n\n {query}\n",
        input_variables=["senddate", "sendfrom", "sendto", "sendcc", "email_body", "query"],
    )
    query = " My name is Mr Chor Wai Tong, a deputy dean (DD) in charge of academic matters in the Faculty of Engineering and Technology (FOET), "\
            " Tunku Abdul Rahman University of Management and Technology (TAR UMT). I am also the coordinator for any audits and risk management. "\
            " Check the entire correspondence my reply is required if any of those mentioned that is to 'all', my name, initials, "\
            " or my work profile as deputy deans or DDs, then " \
            " analyze the mail correspondence and act according to the following criteria: \n" \
            " ** Check if the mail requiring my action or reply (YES/NO). \n " \
            " ** Today is " 
    query += datetime.now().strftime('%b %d, %Y')
    query += " , if it requires my action within two weeks, label it as urgent (YES/NO) \n " \
            " ** If reply is required, propose a consice reply professionally, posing high integrity and intellect. \n "\
            " Your response should be strictly in JSON object with three keys, i.e., 'urgent', 'need_action', and 'draft_reply'. "\
            " An example of the response is : '''{'urgent':'YES', 'need_action':'YES', 'draft_reply':'Dear Dr. Margeret, thanks for your email.'}'''"
    return prompt, query
