from langchain_core.prompts import PromptTemplate
from datetime import datetime

def promptTemplateSkills(listSkillsTags):
    promptTemplateSkills = "You are a helpful assistant named Jarvis " \
    " that interprets instruction from me and issues command using computer language. "  \
    " The followings are the command names, purpose and the function argument: \n" 
    promptTemplateSkills += '\n '.join([x[0] + ' ' + x[1][2] for x in listSkillsTags])
    promptTemplateSkills += "Interpret the given instruction and issue to most appropriate command by" \
            " providing the command name and the argument in JSON object. The json should only contain two keys, i.e., " \
            " the name and the argument." \
            " If there is no good match, issue a sf_talk command, and your response as the argument. "
    return promptTemplateSkills

def promptTemplateMailSummary():
    prompt = PromptTemplate(
        template="Answer the user query.\n Data: \n {dataframe}\n{query}\n",
        input_variables=["dataframe", "query"],
    )
    query = 'Summarize the entire dataframe about mails. Tell me how many mails and their highlights in brief manner.'\
            ' Your text response should be strictly in a paragraph form, no bullet points.'
    return prompt, query

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
            # " ** There is no need to reply to calendar event, or the acceptance of someone on an event. \n "\
            # " ** If reply is required, propose a consice reply professionally. \n "\
            # " Your response should be strictly in JSON object with three keys, i.e., 'urgent', 'need_action', and 'draft_reply'. "\
            # " An example of the response is : '''{'urgent':'YES', 'need_action':'YES', 'draft_reply':'Dear friends, thanks for your email.'}'''"
    return prompt, query
