#Remy Le Breton

"""
Launch arduino with : 

arduino = serial.Serial('/dev/ttyACM0', 19200, timeout=1)
time.sleep(5)

Global variables :
ASK_POS = 'C00000/'    to ask the position

Functions :
launch_command(arduino, code)
convert_steps_in_hex(s)
extract_position(lines)
move_to(pos,bymax=False,topos=True,ask=True)
"""

ASK_POS = 'C00000/'

def launch_command(arduino, code):
    """Launches a command to the arduino"""
    arduino.write(code)
    time.sleep(len(code))
    line = arduino.readlines()
    for i in range(len(line)):
        line[i] = line[i].replace("\r\n","")
    return line

def convert_steps_in_hex(s):
    """Converts a number of step in hexadecimal"""
    if s >= 0:
        step = hex(s)[2:]
        if (len(step) == 1):
            total = "000" + str(step)
            return total
        elif (len(step) == 2):
            total = "00" + str(step)
            return total
        elif (len(step) == 3):
            total = "0" + str(step)
            return total
    elif s < 0:    
        step = hex(65535 + s)[2:]
        return step

def extract_position(lines):
    """Reads and returns the position of the focus in hexadecimal"""
    line = lines[(lines.index([i for i in lines if 'C0' in i][0]) + 1):]
    for i in range(len(line)):
        pos = line[i].find(" ")
        line[i] = line[i][pos+1:]
        line[i] = line[i][-2:]
    
    position = line[0] + line[1]

    return position

def move_to(pos,bymax=False,topos=True,ask=True):
    """
    To move relatively to a position in step coordinate:

    pos : number of step (+ ou - int)
    bymax : if True, goes to focus max before doing the number of steps
    topos : if True, will go to pos
    ask : if True, will ask the position at the end of the movement
    """

    chain = ""
    if bymax:
        chain += "0G060H"
    if topos:
        chain += "0G44" + convert_steps_in_hex(pos) + "0H"
    if ask:
        chain += "C00000"
    chain += "/"
    return chain
