# Automate GMail
This tool feteches all unread mails from the INBOX, then decide whether action/reply is needed using LLM (Gemini). If a reply is needed, then a draft is created. The scanned mail will be removed from INBOX and placed/relabelled with one of these: _AI_general, _AI_urgent, or _AI_need_action.

## Setting up Gmail API
### Steps:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project by following the guide [Create a Google Cloud project ](https://developers.google.com/workspace/guides/create-project)
3. Navigate to **APIs & Services** > **Library** and enable the **Gmail API**.
4. Configure OAuth consent screen:
   - Set up your application name and scope.
   - (optional) Add yourself as a test user.
5. Create credentials:
   - Select **OAuth 2.0 Client IDs**.
   - Download the credentials JSON file and save it as `credentials.json` in the subfolder [\credentials\] of the project directory.
6. The first run of the Gmail auth should create a `token.json` in the subfolder [\credentials\] after going through the auth process via web browser. Remember to allow all scopes on the consent screen.


## Setting up Mailbox
Nothing much, except to create 3 additional labels (you can customize it, just make sure it matches with the code), i.e., `_AI_general_info`, `_AI_need_action`, `_AI_urgent`.

## Customization
1. Customize how the LLM perceive the email, and the persona via the prompt templates in the relevant module. 
