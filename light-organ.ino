/*********************************\

   Arduino Light Organ (backend)

\*********************************/

int pins[] = {10, 9, 8, 7, 6, 5, 4, 3, 2};
char pin;

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 8; i++) pinMode(pins[i], OUTPUT);
  // Reset LPT strobe pin
  digitalWrite(5, LOW);
  digitalWrite(5, HIGH);
}

void loop() {
  while (Serial.available() > 0) {
    pin = Serial.read();
    switch (pin) {
      // Data
      case 'A': digitalWrite(pins[0], HIGH); break;
      case 'B': digitalWrite(pins[1], HIGH); break;
      case 'C': digitalWrite(pins[2], HIGH); break;
      case 'D': digitalWrite(pins[3], HIGH); break;
      case 'E': digitalWrite(pins[4], HIGH); break;
      case 'F': digitalWrite(pins[5], HIGH); break;
      case 'G': digitalWrite(pins[6], HIGH); break;
      case 'H': digitalWrite(pins[7], HIGH); break;
      case 'a': digitalWrite(pins[0], LOW); break;
      case 'b': digitalWrite(pins[1], LOW); break;
      case 'c': digitalWrite(pins[2], LOW); break;
      case 'd': digitalWrite(pins[3], LOW); break;
      case 'e': digitalWrite(pins[4], LOW); break;
      case 'f': digitalWrite(pins[5], LOW); break;
      case 'g': digitalWrite(pins[6], LOW); break;
      case 'h': digitalWrite(pins[7], LOW); break;
    }
  }
}
