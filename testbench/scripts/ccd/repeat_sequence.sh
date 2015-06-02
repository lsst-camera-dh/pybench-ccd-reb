#!/bin/bash
#assuming the right subroutine has been set
while [ 1 ]
do
#triggers sequencer
rriClient 2 write 0x000009  0x00000004
sleep 60
done


