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
   conda env create -f environment.yml -n <env_name>
   ```
   P.S.: For Ana(conda) users, if you encounter some conda verification or corrupt error, ```conda clean --all ``` might help.
3. Activate the environment:
   ```bash
   conda activate <env_name>
   ```

### 2. Follow the following instructions for setting up Gmail automation
Refer to ([README_GMailAPI](https://github.com/chorwaitong/jarvis/blob/main/README_GMailAutomate.md))

### 3. Run the Main Program

Once the setup is complete, you can run the main program:

#### Steps:
1. Ensure the virtual environment is active:
   ```bash
   conda activate <env_name>
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

