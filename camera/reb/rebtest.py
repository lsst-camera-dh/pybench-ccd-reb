
import sys, os, os.path
import time
import subprocess

import lsst.camera.reb as reb
import lsst.camera.reb.fpga as fpga

reb_id = 2

R = reb.REB(reb_id = reb_id)

# loading the functions

# bit 0  : ASPIC RAMP UP
# bit 1  : ASPIC RAMP DOWN
# bit 2  : ASPIC RESET
# bit 3  : ASPIC Clamp

# bit 4  : S1
# bit 5  : S2
# bit 6  : S3
# bit 7  : RG

# bit 8  : P1
# bit 9  : P2
# bit 10 : P3
# bit 11 : P4
# bit 12 : ADC trigger  (convert)

# bit 16 : shutter

# RRRCRRRRPPPPS
# UDSL123G1234T

# function 0 : default state
# rriClient 2 write 0x100000 0x6bc

func = {}

func[0] = \
    fpga.Function(name = "default state",
                  timelengths = {  0 : 2,  # x10ns
                                   1 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000000000011010111100,
                                   1 : 0 } )


# function 1 : shutter function 
# currently just keeping shutter open and clocks in position
# duration 100 us, repeat for exposure time
# cannot have only one timeslice in sequence
# rriClient 2 write 0x100010 0x106BC
# rriClient 2 write 0x100011 0x106BC
# rriClient 2 write 0x200010 10000
# rriClient 2 write 0x200011 2
# rriClient 2 write 0x200012 0

func[1] = \
    fpga.Function(name = "shutter",
                  timelengths = {  0 : 5000,  # x10ns
                                   1 : 5000,
                                   2 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000010000011010111100,
                                   1 : 0b0000000010000011010111100,
                                   2 : 0 } )




# function 2 : line transfer
# should be replaced by crossing transfers when REB can handle it
# rriClient 2 write 0x100020 0x000006BC 
# rriClient 2 write 0x100021 0x00000EBC 
# rriClient 2 write 0x100022 0x00000CBC 
# rriClient 2 write 0x100023 0x00000DBC 
# rriClient 2 write 0x100024 0x000009BC 
# rriClient 2 write 0x100025 0x00000BBC 
# rriClient 2 write 0x100026 0x000003BC 
# rriClient 2 write 0x100027 0x000007BC 
# rriClient 2 write 0x100028 0x000006BC 
# rriClient 2 write 0x200020 100 
# rriClient 2 write 0x200021 1000 
# rriClient 2 write 0x200022 1000 
# rriClient 2 write 0x200023 1000 
# rriClient 2 write 0x200024 1000 
# rriClient 2 write 0x200025 1000 
# rriClient 2 write 0x200026 1000 
# rriClient 2 write 0x200027 1000 
# rriClient 2 write 0x200028 1000
# rriClient 2 write 0x200029 0

func[2] = \
    fpga.Function(name = "line transfer",
                  timelengths = {  0 : 100,  # x10ns
                                   1 : 1000,
                                   2 : 1000,
                                   3 : 1000,
                                   4 : 1000,
                                   5 : 1000,
                                   6 : 1000,
                                   7 : 1000,
                                   8 : 1000,
                                   9 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000000000011010111100,
                                   1 : 0b0000000000000111010111100,
                                   2 : 0b0000000000000110010111100,
                                   3 : 0b0000000000000110110111100,
                                   4 : 0b0000000000000100110111100,
                                   5 : 0b0000000000000101110111100,
                                   6 : 0b0000000000000001110111100,
                                   7 : 0b0000000000000011110111100,
                                   8 : 0b0000000000000011010111100,
                                   9 : 0 } )


# function 3 : pixel read, 2 us
# transcribed from Peter Doherty's Geary setup at Harvard
# increased overlaps from 50 ns to 80 ns
# increased RG up time by 100 ns
# delayed ASPIC RST/CL until second slice so RG is actually up
# first slice lasts one cycle longer than programmed, last slice two cycles
# rriClient 2 write 0x100030 0x6a0
# rriClient 2 write 0x100031 0x6ec
# rriClient 2 write 0x100032 0x64c
# rriClient 2 write 0x100033 0x640
# rriClient 2 write 0x100034 0x641
# rriClient 2 write 0x100035 0x651
# rriClient 2 write 0x100036 0x610
# rriClient 2 write 0x100037 0x612
# rriClient 2 write 0x100038 0x630
# rriClient 2 write 0x100039 0x620
# rriClient 2 write 0x10003a 0x1620
# rriClient 2 write 0x200030 11
# rriClient 2 write 0x200031 18
# rriClient 2 write 0x200032 10
# rriClient 2 write 0x200033 10
# rriClient 2 write 0x200034 42
# rriClient 2 write 0x200035 8
# rriClient 2 write 0x200036 20
# rriClient 2 write 0x200037 50
# rriClient 2 write 0x200038 8
# rriClient 2 write 0x200039 12
# rriClient 2 write 0x20003a 8
# rriClient 2 write 0x20003b 0

func[3] = \
    fpga.Function(name = "read pixel",
                  timelengths = {  0 : 11,  # x10ns
                                   1 : 18,
                                   2 : 10,
                                   3 : 10,
                                   4 : 42,
                                   5 : 8,
                                   6 : 20,
                                   7 : 50,
                                   8 : 8,
                                   9 : 12,
                                  10 : 8,
                                  11 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000000000011010100000,
                                   1 : 0b0000000000000011011101100,
                                   2 : 0b0000000000000011001001100,
                                   3 : 0b0000000000000011001000000,
                                   4 : 0b0000000000000011001000001,
                                   5 : 0b0000000000000011001010001,
                                   6 : 0b0000000000000011000010000,
                                   7 : 0b0000000000000011000010010,
                                   8 : 0b0000000000000011000110000,
                                   9 : 0b0000000000000011000100000,
                                  10 : 0b0000000000001011000100000,
                                  11 : 0 } )


# function 4 : pixel transfer, 2 us
# function with that replicates acquisition timings without ADC trigger
# rriClient 2 write 0x100040 0x6a0
# rriClient 2 write 0x100041 0x6ec
# rriClient 2 write 0x100042 0x64c
# rriClient 2 write 0x100043 0x640
# rriClient 2 write 0x100044 0x641
# rriClient 2 write 0x100045 0x651
# rriClient 2 write 0x100046 0x610
# rriClient 2 write 0x100047 0x612
# rriClient 2 write 0x100048 0x630
# rriClient 2 write 0x100049 0x620
# rriClient 2 write 0x10004a 0x620
# rriClient 2 write 0x200040 11
# rriClient 2 write 0x200041 18
# rriClient 2 write 0x200042 10
# rriClient 2 write 0x200043 10
# rriClient 2 write 0x200044 42
# rriClient 2 write 0x200045 8
# rriClient 2 write 0x200046 20
# rriClient 2 write 0x200047 50
# rriClient 2 write 0x200048 8
# rriClient 2 write 0x200049 12
# rriClient 2 write 0x20004a 8
# rriClient 2 write 0x20004b 0


func[4] = \
    fpga.Function(name = "read pixel (no ADC)",
                  timelengths = {  0 : 11,  # x10ns
                                   1 : 18,
                                   2 : 10,
                                   3 : 10,
                                   4 : 42,
                                   5 : 8,
                                   6 : 20,
                                   7 : 50,
                                   8 : 8,
                                   9 : 12,
                                  10 : 8,
                                  11 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000000000011010100000,
                                   1 : 0b0000000000000011011101100,
                                   2 : 0b0000000000000011001001100,
                                   3 : 0b0000000000000011001000000,
                                   4 : 0b0000000000000011001000001,
                                   5 : 0b0000000000000011001010001,
                                   6 : 0b0000000000000011000010000,
                                   7 : 0b0000000000000011000010010,
                                   8 : 0b0000000000000011000110000,
                                   9 : 0b0000000000000011000100000,
                                  10 : 0b0000000000000011000100000,
                                  11 : 0 } )


# function 5 : fast clear line transfer (as fast as can be with current REB)
# rriClient 2 write 0x100050 0x000006BC 
# rriClient 2 write 0x100051 0x00000CBC 
# rriClient 2 write 0x100052 0x000009BC 
# rriClient 2 write 0x100053 0x000003BC 
# rriClient 2 write 0x100054 0x000006BC 
# rriClient 2 write 0x200050 99
# rriClient 2 write 0x200051 1000 
# rriClient 2 write 0x200052 1000 
# rriClient 2 write 0x200053 1000 
# rriClient 2 write 0x200054 1000 
# rriClient 2 write 0x200055 0 

func[5] = \
    fpga.Function(name = "fast line transfer",
                  timelengths = {  0 : 99,  # x10ns
                                   1 : 1000,
                                   2 : 1000,
                                   3 : 1000,
                                   4 : 1000,
                                   5 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000000000011010111100,
                                   1 : 0b0000000000000110010111100,
                                   2 : 0b0000000000000100110111100,
                                   3 : 0b0000000000000001110111100,
                                   4 : 0b0000000000000011010111100,
                                   5 : 0 })

# function 6 : fast clear serial transfer (900 ns)
# rriClient 2 write 0x100060 0x6ac
# rriClient 2 write 0x100061 0x6ec
# rriClient 2 write 0x100062 0x64c
# rriClient 2 write 0x100063 0x65c
# rriClient 2 write 0x100064 0x61c
# rriClient 2 write 0x100065 0x63c
# rriClient 2 write 0x100066 0x62c
# rriClient 2 write 0x200060 0xe
# rriClient 2 write 0x200061 0x5
# rriClient 2 write 0x200062 0x14
# rriClient 2 write 0x200063 0x5
# rriClient 2 write 0x200064 0x14
# rriClient 2 write 0x200065 0x5
# rriClient 2 write 0x200066 0x12
# rriClient 2 write 0x200067 0

func[6] = \
    fpga.Function(name = "fast serial transfer",
                  timelengths = {  0 : 14,  # x10ns
                                   1 : 5,
                                   2 : 20,
                                   3 : 5,
                                   4 : 20,
                                   5 : 5,
                                   6 : 18,
                                   7 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000000000011010101100,
                                   1 : 0b0000000000000011011101100,
                                   2 : 0b0000000000000011001001100,
                                   3 : 0b0000000000000011001011100,
                                   4 : 0b0000000000000011000011100,
                                   5 : 0b0000000000000011000111100,
                                   6 : 0b0000000000000011000101100,
                                   7 : 0 } )


# function 7 : fast clear while shutter is open (900 ns)
# rriClient 2 write 0x100070 0x106ac
# rriClient 2 write 0x100071 0x106ec
# rriClient 2 write 0x100072 0x1064c
# rriClient 2 write 0x100073 0x1065c
# rriClient 2 write 0x100074 0x1061c
# rriClient 2 write 0x100075 0x1063c
# rriClient 2 write 0x100076 0x1062c
# rriClient 2 write 0x200070 0xe
# rriClient 2 write 0x200071 0x5
# rriClient 2 write 0x200072 0x14
# rriClient 2 write 0x200073 0x5
# rriClient 2 write 0x200074 0x14
# rriClient 2 write 0x200075 0x5
# rriClient 2 write 0x200076 0x12
# rriClient 2 write 0x200077 0

func[7] = \
    fpga.Function(name = "fast serial transfer (open shutter)",
                  timelengths = {  0 : 14,  # x10ns
                                   1 : 5,
                                   2 : 20,
                                   3 : 5,
                                   4 : 20,
                                   5 : 5,
                                   6 : 18,
                                   7 : 0 },
                  #                    
                  #                      ........S...SPPPPRSSSCRRR
                  #                      ........H...T4321G321LSDU
                  outputs =     {  0 : 0b0000000010000011010101100,
                                   1 : 0b0000000010000011011101100,
                                   2 : 0b0000000010000011001001100,
                                   3 : 0b0000000010000011001011100,
                                   4 : 0b0000000010000011000011100,
                                   5 : 0b0000000010000011000111100,
                                   6 : 0b0000000010000011000101100,
                                   7 : 0 } )

# id_funcs = func.keys()
# id_funcs.sort()
# for id_func in id_funcs:
#     R.load_function(id_func, func[id_func])

R.load_functions(func)


program = """
main:        JSR     acq            repeat(1)
             END 

acq:         JSR     clear          repeat(2)
             CALL    func(1)        repeat(10000)
             CALL    func(6)        repeat(2048)
             JSR     read_line      repeat(2020)
             RTS 

clear:       JSR     clear_line     repeat(2020)
             RTS 

clear_10:    JSR     clear          repeat(10)
             RTS 

clear_bias:  JSR     clear          repeat(2)
             CALL    func(6)        repeat(550)
             JSR     read_line      repeat(2020)
             RTS 

acq_fake:    JSR     clear          repeat(2)
             CALL    func(1)        repeat(10000)
             CALL    func(6)        repeat(1100)
             JSR     read_line_fake repeat(2020)
             RTS 

bias:        CALL    func(6)        repeat(550)
             JSR     read_line      repeat(2020)
             RTS 

clear_acq:   JSR     clear          repeat(2)
             # exposure while clearing 
             # (call expo_clear: 1 time = 100 us, up to 17 bits, here 4E20 = 2s)
             JSR     expo_clear     repeat(20000)
             # before readout : flush serial register again twice (0x44c)
             CALL    func(6)        repeat(1100)
             JSR     read_line      repeat(2020)
             RTS 

# auxiliary subroutine: exposure while clearing 
# duration 100 us (for consistency with exposure without clearing)

expo_clear:  CALL    func(7)        repeat(50)
             RTS 

read_line:   CALL    func(2)        repeat(1)     # line transfer 
             # read 550 pixels (10 prescan + 512 + 28 overscan)
             CALL    func(3)        repeat(550)   
             RTS 

clear_line:  CALL    func(5)        repeat(1)
             CALL    func(6)        repeat(550)
             RTS 

read_line_fake: 
             CALL    func(2)        repeat(1)     # line transfer 
             # read 550 pixels (10 prescan + 512 + 28 overscan)
             CALL    func(4)        repeat(550)
             RTS 
"""


# loading the default sequencer program
R.load_program(program)

# Compute image size and configure the REB accordingly
# It should be computed for a given sub_routine
## image_size = R.count_subroutine('acq', bit = 12, transition = 'up')
# rriClient 2 write 0x400005 0x0010F3D8
R.set_image_size(2020 * 550)

# starting the clock register
R.fpga.start_clock()

# starting the imageClient process (requested!)
# subprocess.Popen("imageClient %d" % reb_id) -> path problem
# subprocess.Popen("imageClient %d" % reb_id, shell=True)

# launching a clear 10 times
R.run_subroutine('clear', repeat = 10)

# taking a bias
time.sleep(1)
R.run_subroutine('bias')

# taking a frame
time.sleep(15)
R.run_subroutine('acq')


