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
    query = " My name is Mr Chor Wai Tong, a deputy dean (DD) in charge of academic matters in the Faculty of Engineering and Technology (FOET), "\
            " Tunku Abdul Rahman University of Management and Technology (TAR UMT). I am also the coordinator for any audits and risk management. "\
            " Check the entire correspondence my reply is required if any of those mentioned that is to 'all', my name, initials, "\
            " or my work profile as deputy deans or DDs, then " \
            " analyze the mail correspondence and act according to the following criteria: \n" \
            " ** Check if the mail requiring my action or reply (YES/NO). \n " \
            " ** Today is " 
    query += datetime.now().strftime('%b %d, %Y')
    query += " , if it requires my action within two weeks, label it as urgent (YES/NO) \n " \
            " Your response should be strictly in JSON object with two keys, i.e., 'urgent' and 'need_action'. "\
            " An example of the response is : '''{'urgent':'YES', 'need_action':'YES'}'''"
            # " ** There is no need to reply to calendar event, or the acceptance of someone on an event. \n "\
            # " ** If reply is required, propose a consice reply professionally. \n "\
            # " Your response should be strictly in JSON object with three keys, i.e., 'urgent', 'need_action', and 'draft_reply'. "\
            # " An example of the response is : '''{'urgent':'YES', 'need_action':'YES', 'draft_reply':'Dear Dr. Margeret, thanks for your email.'}'''"
    return prompt, query

def promptTemplateCPDDecision():
    prompt = PromptTemplate(
    template = ''' [Guideline of CPD hours application] \n
                    The CPD (Continuous Professional Development) system allocates points to various activities based on predefined categories and criteria. Below are the detailed descriptions for each category:
            1. Congresses and Conferences:
            Attending local or international congresses and conferences earns CPD points based on duration. Half-day attendance (3 hours) provides 3 points, full-day attendance (5–8 hours) provides 6 points, and participation in conferences spanning 2–3 full days awards 10 points. Annual maximum points: 20.
            2. Scientific and Technical Meetings:
            Participation in meetings organized by accredited CPD providers that are relevant to technical and professional development is worth 2 points per day. Annual maximum points: 10.
            3. Workshops, Courses, Fellowships, and Study Tours:
            CPD points vary based on the duration and nature of workshops or hands-on skills training. Half-day activities earn 3 points, full-day activities earn 6 points, and programs lasting 2 or more days provide 10 points. Study tours earn 5 points per tour. Annual maximum points: 15.
            4. Continuous Education Sessions:
            Engaging in seminars, forums, lectures, journal clubs, and research updates offers 2 points per session. Points are also awarded for committee involvement in organizing these activities. Annual maximum points: 5.
            5. Presentations at Accredited Meetings:
            Delivering plenary or keynote lectures earns 15 points, while oral or poster presentations award 10 points. Panelists, moderators, or chairs earn 5 points. These points are supplemental to attendance points. Annual maximum points: 30.
            6. Publications:
            CPD points are granted for publishing in journals or contributing to books. Indexed journal articles (ISI/WOS/SCOPUS) earn 20 points for the main author and 10 for co-authors. 
            Journal articles indexed with ERA/MyCite earn 10 points for the main author and 5 for co-authors. 
            Non-indexed journals, technical reports, and bulletins earn 5 and 3 points for main author and co-author respectively. Annual maximum points: 40.
            If the applicant is not within the first six authors, then no CPD points will be awarded.
            7. Research Patents:
            Points are awarded for filing (3 points), pending (5 points), granted (15 points), or commercialized/licensed patents (30 points). Annual maximum points: 30.
            8. Post-Doctorate Training:
            Training durations influence CPD points: 1–2 weeks (10 points), 2–4 weeks (12 points), 1–3 months (15 points), 3–6 months (20 points), and over 6 months to 1 year (30 points). Annual maximum points: 30.
            9. Formal Education:
            Formal studies, such as pursuing a Master’s degree or PhD, earn 10 points per year. Professional certifications earn 5 points upon completion. Annual maximum points: 40 (cumulative for Master’s/PhD) or 20 (professional certifications).
            10. Consultancy or Research Projects:
            Participation in projects as a principal investigator (PI) or member grants points based on duration. Short-term projects (<6 months) award 6 points (PI) or 3 points (member). Medium-term projects (6 months–1 year) provide 8 points (PI) or 4 points (member). Long-term projects (1–2 years) award 10 points (PI) or 5 points (member). Training as a facilitator or trainer earns 5 points. Annual maximum points: 20.
            11. Appointment as Assessor or Examiner:
            Serving as an assessor, external examiner, or advisor grants points based on the role: 8 points for full accreditation, 5 points for provisional accreditation, and 3–4 points for other roles. Annual maximum points: 15.
            12. Editorial and Review Activities:
            Serving as an editor for journals or reports earns 10 points, while members of editorial boards or referees for individual articles earn 5 points per activity. Annual maximum points: 15.
            13. Supporting Activities and Personal Development:
            Activities such as committee memberships in professional bodies, involvement in associations, and participation in local, national, or international programs grant points based on level: 5 points for local/state/national activities, and 10 points for international activities. Membership grades also influence points. Annual maximum points: 20.
            14. Online Learning:
            Participation in online webinars, workshops, and training sessions awards points based on duration: 1 point (1–2 hours), 2 points (half day), 3 points (full day), 6 points (2 days), and 8 points (>2 days). Annual maximum points: 20.
            15. Mentoring, Coaching, Judging and Outreach:
            Be appointed as the mentor, coach, or judge earn points based on the level of engagement: 12 points for world-level activities, 8 for ASEAN-level, and 5 for national-level activities. Such mentoring/supervison/judging activities should be confined to external activities not typical undergraduate or postgraduate supervision.  Annual maximum points: 15. \n
            
            Next is the detail of an activity:
            [Activity Details]
            {activity}
            
            Answer the user query considering the above activity, and the criteria on the allocation of CPD hours.\n
            {query}
            ''', input_variables = ["activity", "query"]
            )
    query = '''Provide the CPD point of the activity along with an explanation.
               Raise red_flag (YES/NO) with clear explaination if the activity meet any one of the following criteria:
                   ** The total number of authors exceed 6 for a journal article.
                   ** Any inconsistencies of the details provided. 
                Your response should be strictly in JSON object with three keys, i.e., the CPD_point, red_flag and explanation, an example would be as follows:\n
                 {'CPD_point':5, 'red_flag': NO ,'explanation': The activity regards to a pending research patent, therefore it worth 5 points.} 
                        '''
    return prompt, query