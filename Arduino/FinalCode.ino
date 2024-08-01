#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

#define SAMPLE_RATE 125
#define MAX_SIZE 250
#define BAUD_RATE 115200
#define INPUT_PIN A0
#define LEADS_OFF_POS D1
#define LEADS_OFF_NEG D2

const char* sta_ssid = "Kali";
const char* sta_password = "y=e^(cos(xy))";

const char* ap_ssid = "ECG_Device";
const char* ap_password = "123456";

bool createAP = false;

IPAddress local_ip(192,168,1,1);
IPAddress gateway(192,168,1,1);
IPAddress subnet(255,255,255,0);

ESP8266WebServer server(80);

struct Node
{
    int value;
    Node *next;
    Node *prev;
};

Node *head = nullptr;
Node *tail = nullptr;
int currentSize = 0;

bool Check_Leads() {
  bool ERR = (digitalRead(LEADS_OFF_POS) == 1) || (digitalRead(LEADS_OFF_NEG) == 1);
  if (ERR) {
    Serial.println("ERROR!!");
  }
  return !ERR;
}

int Read_Sensor() {
  if (!Check_Leads()) { return -1; }
  return analogRead(INPUT_PIN);
}

void addToHead(int value)
{
    Node *newNode = new Node;
    newNode->value = value;
    newNode->next = head;
    newNode->prev = nullptr;

    if (head != nullptr)
    {
        head->prev = newNode;
    }
    head = newNode;

    if (currentSize == 0)
    {
        tail = newNode;
    }

    currentSize++;

    if (currentSize > MAX_SIZE)
    {
        removeTail();
    }
}

void removeTail()
{
    if (!tail)
        return;

    if (head == tail)
    {
        delete tail;
        head = nullptr;
        tail = nullptr;
    }
    else
    {
        Node *newTail = tail->prev;
        newTail->next = nullptr;
        delete tail;
        tail = newTail;
    }

    currentSize--;
}

void PrintList()
{
    Node *current = head;
    while (current)
    {
        Serial.print(current->value);
        Serial.print(" <-> ");
        current = current->next;
    }
    Serial.println("NULL");
}

float ECGFilter(float input)
{
    float output = input;
    {
        static float z1, z2;
        float x = output - 0.70682283 * z1 - 0.15621030 * z2;
        output = 0.28064917 * x + 0.56129834 * z1 + 0.28064917 * z2;
        z2 = z1;
        z1 = x;
    }
    {
        static float z1, z2;
        float x = output - 0.95028224 * z1 - 0.54073140 * z2;
        output = 1.00000000 * x + 2.00000000 * z1 + 1.00000000 * z2;
        z2 = z1;
        z1 = x;
    }
    {
        static float z1, z2;
        float x = output - -1.95360385 * z1 - 0.95423412 * z2;
        output = 1.00000000 * x + -2.00000000 * z1 + 1.00000000 * z2;
        z2 = z1;
        z1 = x;
    }
    {
        static float z1, z2;
        float x = output - -1.98048558 * z1 - 0.98111344 * z2;
        output = 1.00000000 * x + -2.00000000 * z1 + 1.00000000 * z2;
        z2 = z1;
        z1 = x;
    }
    return output;
}

void setupAP() {
    WiFi.softAP(ap_ssid, ap_password);
    WiFi.softAPConfig(local_ip, gateway, subnet);
    
    Serial.println("Access Point Started");
    Serial.print("IP Address: ");
    Serial.println(WiFi.softAPIP());
}

void setupSTA() {
    WiFi.begin(sta_ssid, sta_password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    
    Serial.println("Connected to WiFi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
}

void setup()
{
    Serial.begin(BAUD_RATE);
    
    if (createAP) {
        setupAP();
    } else {
        setupSTA();
    }

    server.on("/getECGData", handleGetECGData);
    server.begin();
    Serial.println("HTTP server started");

    pinMode(INPUT_PIN, INPUT);
    pinMode(LEADS_OFF_POS, INPUT);
    pinMode(LEADS_OFF_NEG, INPUT);
}

void handleGetECGData() {
    String response = "[";
    Node* current = head;
    int count = 0;
    bool hasError = false;

    while (current && count < 125) {
        if (current->value == -1) {
            hasError = true;
            break;
        }
        response += String(current->value);
        if (count < 124) {
            response += ", ";
        }
        current = current->next;
        count++;
    }

    response += "]";
    
    if (hasError) {
        server.send(400, "application/json", "{\"error\": \"Invalid data detected\"}");
    } else {
        server.send(200, "application/json", response);
    }
}

void loop()
{
    static unsigned long past = 0;
    unsigned long present = micros();
    unsigned long interval = present - past;
    past = present;

    static long timer = 0;
    timer -= interval;

    if (timer < 0)
    {
        server.handleClient();
        timer += 1000000 / SAMPLE_RATE;
        int sensor_value = Read_Sensor();
        if (sensor_value != -1) {
            float signal = ECGFilter(sensor_value);
            addToHead(signal);
        } else {
            addToHead(-1);
        }
    }
}