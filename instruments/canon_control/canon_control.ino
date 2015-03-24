/*
  Blink
  Turns on an LED on for one second, then off for one second, repeatedly.
 
  This example code is in the public domain.
 */

#include <SPI.h>
// Pin 13 has an LED connected on most Arduino boards.
// give it a name:
//int ledPin = 13;
int detPin = 2;
int vddPin = 10;
int vpowPin = 9;
bool det = HIGH;
bool state = HIGH;
const int chipSelectPin = 4;
void isr(){
   det = digitalRead(detPin);
}

char send(char command){
  char answer;
  answer = SPI.transfer(command);
  delay(10);
  return answer;
}

void init_lens(){
   char answers[51];
   for (int j=0; j<51; j++){ 
      answers[j] = send(0x00);
   }
   answers[0] = send(0x0A);
   answers[1] = send(0x00);
   answers[2] = send(0x0A);
   answers[3] = send(0x00);
   answers[4] = send(0x80);
   answers[5] = send(0x0A);
   answers[6] = send(0x97);
   answers[7] = send(0x01);
   for (int j=8; j<19; j++)
   {
     answers[j] = send(0x00); 
   }
   
   // Send the answer to the serial port
   for (int j=0; j<19; j++){ 
     Serial.print(answers[j], DEC);   
     Serial.print("/");
   }
   Serial.println("/");

}


void focus_move(char what){
   
   char answers[7];

   // Poll the lens
   answers[0] = send(0x0A);
   answers[1] = send(0x00);

   // Power On focus motor
   digitalWrite(vpowPin, LOW);
   
   // Turn focus ring to AF min or max
   if (what == 'd'){
     Serial.println("Moving to focus min");
      answers[2] = send(0x05);
      delay(1000);
   }
   else if (what == 'u'){
     Serial.println("Moving to focus max");
      answers[2] = send(0x06);
      delay(1000);
    }
   else if (what == '+'){
      Serial.println("Moving step up");
       answers[2] = send (0x44);
       answers[3] = send (0x00);
       answers[4] = send (0x01);
       delay(100);
   }
   else if (what == '-'){
           Serial.println("Moving step down");
       answers[2] = send (0x44);
       answers[3] = send (0xFF);
       answers[4] = send (0xFF);
       delay(100);
   }
   else if (what == 'q'){
      Serial.println("Moving step up");
       answers[2] = send (0x44);
       answers[3] = send (0x00);
       answers[4] = send (0x0A);
       delay(100);
   }
   else if (what == 's'){
           Serial.println("Moving step down");
       answers[2] = send (0x44);
       answers[3] = send (0xFF);
       answers[4] = send (0xF6);
       delay(100);
   }
   // Wait a bit
   

   // Power down
   digitalWrite(vpowPin, LOW);

   // Poll the lens
   answers[5] = send(0x0A);
   answers[6] = send(0x00);

   for (int j=0; j < 7; j++){
     Serial.print(answers[j], DEC);   
     Serial.print("/");
   }
   Serial.println("/");
}



void setup() {                
  // initialize digital pins and interrution
  //pinMode(ledPin, OUTPUT);
  pinMode(detPin, INPUT_PULLUP);
  pinMode(vddPin, OUTPUT);
  pinMode(vpowPin, OUTPUT);
  digitalWrite(vddPin, HIGH);		
  digitalWrite(vpowPin, HIGH);
  attachInterrupt(0, isr, CHANGE);
  delay(300);
  
  // Change frequency to 8MHz to get SPI communication at 62kHz
  CLKPR = B10000000; 
  CLKPR = B00000001;

  // Set up SPI
  pinMode(chipSelectPin, OUTPUT);
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setClockDivider(SPI_CLOCK_DIV128);
  SPI.setDataMode(SPI_MODE3);
  digitalWrite(12, HIGH); // Pull-up DCL

  // Serial port initialization 19200
  Serial.begin(38400);
  
}

void loop() {
  if (det != state){
    if (det == LOW){
      delay(1000);
      if (det == LOW){
        //digitalWrite(ledPin, HIGH);
	digitalWrite(vddPin, LOW);
	//digitalWrite(vpowPin, LOW);
   	state = LOW;
        Serial.println("Lens detected, init...");	
	delay(300);
	init_lens();
      }
    }
   else{
     //digitalWrite(ledPin, LOW);    // turn the LED off by making the voltage LOW
     digitalWrite(vddPin, HIGH);
     //digitalWrite(vpowPin, HIGH);
     state = HIGH;
   }
  }
  else if(state == LOW) {
    if (Serial.available() > 0){
      char incomingByte = Serial.read();
      switch(incomingByte){
        case 'd':
        focus_move('d');
        break;
        case 'u':
        focus_move('u');
        break;
        case 'a':
        focus_move('+');
        break;
        case 'z':
        focus_move('-');
        break;
        case 'q':
        focus_move('q');
        break;
        case 's':
        focus_move('s');
        break;
        case 'p':
        init_lens();
        break;
        
      }
    }
  }
}
