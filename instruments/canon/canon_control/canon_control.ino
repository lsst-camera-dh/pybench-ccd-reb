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

char buffer[100];
int index = 0;

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
   if (what == '<'){
     Serial.println("Moving to focus min");
      answers[2] = send(0x05);
      delay(1000);
   }
   else if (what == '>'){
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
   else if (what == 'h'){
           Serial.println("Asking zoom value");
       answers[2] = send (0xA0);
       answers[3] = send (0x00);
       answers[4] = send (0x00);
       delay(100);
   }
   else if (what == 'x'){
           Serial.println("Asking USM motor counter position");
           answers[2] = send (0xC0);
           answers[3] = send (0x00);
           answers[4] = send (0x00);
          delay(100);
   }
   // Wait a bit
   

   // Power down
   digitalWrite(vpowPin, HIGH); //put HIGH instead of LOW for power down

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

void executeCommand(char buffer[], int & index)
{
       int k = 0;
       int secure = 0;
       while(buffer[k]!='/')
           {
                 char instruction[4];
                 instruction[0] = '0';
                 instruction[1] = 'x';
                 instruction[2] = buffer[k];
                 instruction[3] = buffer[k+1];
                 
                 if(buffer[k]=='0' && buffer[k+1]=='G')
                     {
                     //Before sending amoving command, power up of the motor.
                     digitalWrite(vpowPin, LOW);
                     delay(100);
                     }
                 else if(buffer[k]=='0' && buffer[k+1]=='H')
                     {
                       //After sending a moving command, power off of the motor
                       delay(500);
                       digitalWrite(vpowPin, HIGH);
                       delay(100);
                     }
                 else
                     {
                       unsigned char a = 0;
                       unsigned int d = 0;
                       sscanf(instruction, "%x", &d);
                       a = (unsigned char)d;
                       
                       //Serial.print("Command : ");  
                       Serial.print(a, HEX);
                       Serial.print(" ");
                       //Serial.print("  Answer : ");
                       Serial.println(send(a), HEX);
                     }
                
                 if(secure == 150)
                 {
                       break;
                 }
                 
                 k = k + 2;
                 secure = secure + 1;
           }
       //Serial.println("Command executed, reinitializing buffer...");
       eraseBuffer(buffer,index);
}

void eraseBuffer(char buffer[], int & index)
{
      for(int j = 0; j < 100; j++)
           {
                   buffer[j] = 0;
            }
      index = 0;
}

void loop() {
  isr();
  //Serial.print("state, det = ");
  //Serial.print(state, DEC); 
  //Serial.print(det, DEC); 
  //Serial.println(""); 
  //delay(200);
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
        case '<':
        focus_move('<');
        break;
        case '>':
        focus_move('>');
        break;
        case '+':
        focus_move('+');
        break;
        case '-':
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
        case 'h':
        focus_move('h');
        break;
        case 'x':
        focus_move('x');
        break;
        case '/':
              if(index > 1 && !(index%2))
              {
                      buffer[index] = incomingByte;
                      
                      //Serial.print("Poll the lens : ");
                      //Serial.print("Command : 0A-");
                      send(0x0A);
                      //Serial.print("  Answer : ");
                      send(0x00);
                      
                      executeCommand(buffer,index);
                      
              }
              else
              {
                  Serial.println("Warning : Command need even number of element");
                  Serial.println("Buffer not reinitialized");
              }
        break;
        default:
              if(index<100)
              {
                   if(((incomingByte >= '0') && (incomingByte <= '9')) ||
                       ((incomingByte >= 'A') && (incomingByte <= 'H')) || 
                       ((incomingByte >= 'a') && (incomingByte <= 'h')))
                   {
                                      buffer[index]= incomingByte;
                                      index = index + 1;
                                      //Serial.println(buffer);
                                      //Serial.print("  ");
                                      //Serial.println(index);
                                      //Serial.println(index%2);
                                      break;
                    }
                    else
                    {
                      Serial.println("Invalid caracter detected, command aborted...");
                      eraseBuffer(buffer,index);
                    }
              }
              else
              {
                    Serial.println("Command sequence too long (>100), command aborted...");
                    eraseBuffer(buffer,index);
              }
        break;
      }
    }
  }
}

