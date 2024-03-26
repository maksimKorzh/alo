int pins[] = {13, 12, 10, 9, 8, 7, 6, 5};
char pin;

void setup() {
  // initialize serial:
  Serial.begin(115200);

  for (int i = 0; i < 8; i++) pinMode(pins[i], OUTPUT);
}

void loop() {
  while (Serial.available() > 0) {
	  pin = Serial.read();
    switch (pin) {
      case 'a': digitalWrite(13, HIGH); break;
      case 'b': digitalWrite(12, HIGH); break;
      case 'c': digitalWrite(11, HIGH); break;
      case 'd': digitalWrite(10, HIGH); break;
      case 'e': digitalWrite(9, HIGH); break;
      case 'f': digitalWrite(8, HIGH); break;
      case 'g': digitalWrite(7, HIGH); break;
      case 'h': digitalWrite(6, HIGH); break;
      case 'A': digitalWrite(13, LOW); break;
      case 'B': digitalWrite(12, LOW); break;
      case 'C': digitalWrite(11, LOW); break;
      case 'D': digitalWrite(10, LOW); break;
      case 'E': digitalWrite(9, LOW); break;
      case 'F': digitalWrite(8, LOW); break;
      case 'G': digitalWrite(7, LOW); break;
      case 'H': digitalWrite(6, LOW); break;
    }
  }
}
