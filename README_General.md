# Jarvis

The project **Jarvis** is a long-term personal project aimed at automating virtually everything. In this humble beginning, the current focus is on automating work email management using Gemini LLM-based LangChain, Gmail API, and Python.

---

## Features
- Intelligent email automation using Gemini LLM.
- Seamless integration with Gmail API.
- Modular and extensible design for future automation features.

---

## Getting Started

Follow the steps below to set up and run the project.

### 1. Create the Environment

To ensure compatibility and reproducibility, create a virtual environment using the provided `environment.yml` file.

#### Steps:
1. Clone this repository:
   ```bash
   git clone https://github.com/chorwaitong/jarvis.git
   cd jarvis
   ```
2. Create the environment:
   ```bash
   conda env create --name jarvis -f environment.yml
   ```
3. Activate the environment:
   ```bash
   conda activate jarvis
   ```

### 2. Set Up Google Project and Enable Gmail API
Refer to README_GMailAPI

### 3. Create Gemini LLM API Key

#### Steps:
1. Sign up or log in to the [Gemini AI Studio](https://aistudio.google.com/app/apikey).
2. Generate an API key from the dashboard.
3. Save the API key, you can consider saving it as an environment variable for security (sorry I didn't opt this).

### 4. Run the Main Program

Once the setup is complete, you can run the main program:

#### Steps:
1. Ensure the virtual environment is active:
   ```bash
   conda activate jarvis
   ```
2. Run the program:
   ```bash
   python main.py
   ```

---

## Future Scope
- Expand automation capabilities to handle calendar scheduling, task management, and data analysis.
- Integrate additional APIs and frameworks.
- Improve the learning and adaptability of Jarvis through advanced AI techniques.

---

## Contributing
Contributions are welcome! Feel free to fork the repository and submit a pull request.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

