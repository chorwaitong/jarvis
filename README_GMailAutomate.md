# Setting up Gmail API
## Steps:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project by following the guide [Create a Google Cloud project ](https://developers.google.com/workspace/guides/create-project)
3. Navigate to **APIs & Services** > **Library** and enable the **Gmail API**.
4. Configure OAuth consent screen:
   - Set up your application name and scope.
   - Add yourself as a test user.
5. Create credentials:
   - Select **OAuth 2.0 Client IDs**.
   - Download the credentials JSON file and save it as `credentials.json` in the subfolder [\credentials\] of the project directory.
6. The first run of the Gmail auth should create a 'token.json' in the subfolder [\credentials\] after going through the auth process via web browser.

# Setting up Gemini API
## Steps:
1. Sign up or log in to the [Gemini AI Studio](https://aistudio.google.com/app/apikey).
2. Generate an API key from the dashboard.
3. Save the API key as an environment variable with name "GOOGLE_API_KEY".

# Setting up Mailbox
Nothing much, except to create 3 additional labels (you can customize it, just make sure it matches with the code), i.e., _AI_general_info, _AI_need_action, _AI_urgent.

# Edit codes
1. 
