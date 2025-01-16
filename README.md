<a href="https://www.buymeacoffee.com/chorwaitong" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

# Jarvis

Watch in Youtube:

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/gwRaSlDPZv8/0.jpg)](https://www.youtube.com/watch?v=gwRaSlDPZv8&ab_channel=ChorWT)

The project **Jarvis** is a long-term personal project aimed at controlling/ automating virtually everything. In this humble beginning, the current focuses includes the following features with Gemini LLM-based LangChain, Gmail API, MQTT, and Python.

---

## Features
- Desktop/computer controls such as opening music, apps, searching via web browser, etc.
- MQTT IoT Device control, a simple one (relay control light) for now.
- Intelligent email automation using Gemini LLM.
- Integration with Gmail API.
- Modular and extensible design for future automation features.

---

## Getting Started

### Hardware:
- ESP8266 + Relay = Bought from ([Tao Bao](https://e.tb.cn/h.TkVHVR1RKvf5a5o?tk=tzGLedFIfD3))
- 
### Software:
Follow the steps below to set up and run the project.

#### 1. Create the Environment

To ensure compatibility and reproducibility, create a virtual environment using the provided `environment.yml` file.

##### Steps:
1. Clone this repository:
   ```bash
   git clone https://github.com/chorwaitong/jarvis.git
   cd jarvis
   ```
   [Guide to install Git](https://github.com/git-guides/install-git)

   to update:
   ```bash
   git pull origin main
   ```
   
3. Create the environment (I'm using Anaconda):
   ```bash
   conda env create -f environment.yml -n <env_name>
   ```
   P.S.: For Ana(conda) users, if you encounter some conda verification or corrupt error, ```conda clean --all ``` might help.
4. Activate the environment:
   ```bash
   conda activate <env_name>
   ```

#### 2. Follow the following instructions for setting up stuffs
- Gmail and Gemini API Access: Refer to ([README_GMailAPI](https://github.com/chorwaitong/jarvis/blob/main/README_GMailAutomate.md))
- For MQTT-based control of IoT devices, sign up for an MQTT Broker account, I am using HiveMQ Cloud: Refer ([HiveMQ Cloud](https://docs.hivemq.com/hivemq-cloud/quick-start-guide.html)). Next, store the credentials as environment variables as `MQTT_USERNAME` and `MQTT_PASSWORD`.  
  
#### 3. Run the Main Program

Once the setup is complete, you can run the main program by running:
   ```bash
   run.bat
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

