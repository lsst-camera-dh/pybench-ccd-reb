/*
  Blink
  Turns on an LED on for one second, then off for one second, repeatedly.
 
  This example code is in the public domain.
 */

#include <SPI.h>
#include <string.h>

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

void setup() {                
  // initialize digital pins and interrution
  //pinMode(ledPin, OUTPUT);
  pinMode(detPin, INPUT_PULLUP);
  pinMode(vddPin, OUTPUT);
  pinMode(vpowPin, OUTPUT);
  digitalWrite(vddPin, HIGH);		
  digitalWrite(vpowPin, HIGH);
  attachInterrupt(0, isr, CHANGE);
   //attachInterrupt(0, isr, LOW);
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
  //isr();
  int sensorVal = digitalRead(2);
  Serial.print("state, det = ");
  Serial.print(state, DEC); 
  Serial.print(det, DEC); 
  Serial.println(""); 
  delay(200);

  if (det != state){
     if (det == LOW){
        delay(1000);
        if (det == LOW){
          //digitalWrite(ledPin, HIGH);
	  digitalWrite(vddPin, LOW);
	  //digitalWrite(vpowPin, LOW);
   	  state = LOW;
          Serial.println("Lens detected, init...");
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
      Serial.print("incomingByte = ");
      Serial.println(incomingByte, HEX);
    }
  }
}


