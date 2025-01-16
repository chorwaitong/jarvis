#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>

const char* ssid = ;//wifi-ssid;
const char* password = ;//wifi-password;

// MQTT Broker settings
const char* mqtt_broker = ;// Place the broker url here, e.g. "xxxx.s1.eu.hivemq.cloud";  
const char* mqtt_topic = "home/bedroom/light1";
const char* mqtt_val_topic = "home/bedroom/light1/val"; 
const char* mqtt_username = ; //place the username obtained from the broker console. ;  
const char* mqtt_password = ; //place the password obtained from the broker console. ;   
const int mqtt_port = 8883;  

WiFiClientSecure espClient;
PubSubClient mqtt_client(espClient);

const int relayPin = 0;
bool relayStatus;

void writeRelay(bool);
void connectToWiFi();
void connectToMQTTBroker();
void mqttCallback(char *topic, byte *payload, unsigned int length);

void writeRelay(bool relay_on)
{
  relayStatus = relay_on;
  if (relay_on) {
    digitalWrite(relayPin, 0);
  }
  else {
    digitalWrite(relayPin, 1);    
  }
  delay(100);
  mqttRespond();
}

void mqttRespond(){
  int pinState = digitalRead(relayPin);
  pinState = 1- pinState; 
  mqtt_client.publish(mqtt_val_topic,  String(pinState).c_str());
}

void connectToWiFi() {
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\nConnected to the WiFi network");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
}

void connectToMQTTBroker() {
    while (!mqtt_client.connected()) {
        String client_id = "client-";
        client_id += String(random(0xffff), HEX);
        Serial.printf("Connecting to MQTT Broker as %s.....\n", client_id.c_str());
        if (mqtt_client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("Connected to MQTT broker");
            mqtt_client.subscribe(mqtt_topic);
            mqtt_client.subscribe(mqtt_val_topic);
            mqttRespond();
        } else {
            Serial.print("Failed to connect to MQTT broker, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
    String message;
    for (unsigned int i = 0; i < length; i++) {
      message += (char) payload[i];
    }
    if ((String(topic) == mqtt_val_topic) && (message == "") ){
      Serial.println("Received Health Check");
      mqttRespond();
    }else if (String(topic) == mqtt_topic){
      if (message == "1"){
        writeRelay(true);
        Serial.println("Relay on");
      }else{
        writeRelay(false);
        Serial.println("Relay off");
      }
    }  
}

void setup() {
    pinMode(relayPin, OUTPUT);
    writeRelay(true);
    Serial.begin(115200);
    connectToWiFi();
    espClient.setInsecure();
    mqtt_client.setServer(mqtt_broker, mqtt_port);
    mqtt_client.setCallback(mqttCallback);
    connectToMQTTBroker();
}

void loop() {
    if (!mqtt_client.connected()) {
        connectToMQTTBroker();
    }
    mqtt_client.loop();
}
