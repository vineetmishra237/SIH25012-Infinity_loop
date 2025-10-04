#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

#define RST_PIN D3
#define SS_PIN  D4
MFRC522 mfrc522(SS_PIN, RST_PIN);

#define RED_LED   D0
#define GREEN_LED D1
/* Boot/ WiFi connecting → both blink slowly.
Ready (connected to WiFi) → Green solid ON.
RFID card detected → Red blinks once.
Sending UID → Green blinks fast.
Success response from server → Green blinks 3 times.
Error response/ failure → Red blinks 3 times.*/

const char* ssid = "JioFib5G";
const char* password = "********";
const char* serverURL = "http://192.168.29.130:5000/api/rfid_scan";

WiFiClient client;

void blinkLED(int pin, int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(delayMs);
    digitalWrite(pin, LOW);
    delay(delayMs);
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);

  // Start SPI bus and RFID
  SPI.begin();
  mfrc522.PCD_Init();

  Serial.println("Booting...");

  // Blink both LEDs while connecting to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    blinkLED(RED_LED, 1, 300);
    blinkLED(GREEN_LED, 1, 300);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Green solid ON means ready
  digitalWrite(GREEN_LED, HIGH);
}

void loop() {
  // Look for new card
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Build UID string
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toLowerCase(); // ensure lowercase

  Serial.print("Card detected, UID: ");
  Serial.println(uid);

  // Blink red once to show card read
  blinkLED(RED_LED, 1, 150);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, serverURL);
    http.addHeader("Content-Type", "application/json");

    String json = "{\"uid\":\"" + uid + "\"}";

    Serial.print("Sending UID to server: ");
    Serial.println(json);

    // Blink green fast while sending
    blinkLED(GREEN_LED, 2, 100);

    int httpResponseCode = http.POST(json);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("Server response code: ");
      Serial.println(httpResponseCode);
      Serial.print("Response body: ");
      Serial.println(response);

      if (httpResponseCode == 200) {
        blinkLED(GREEN_LED, 3, 200);
      } else {
        Serial.println("⚠️ Server error / mismatch!");
        blinkLED(RED_LED, 3, 200);
      }
    } else {
      Serial.print("HTTP Request failed: ");
      Serial.println(http.errorToString(httpResponseCode).c_str());
      blinkLED(RED_LED, 5, 100);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected!");
    blinkLED(RED_LED, 2, 400);
  }

  delay(2000);
}