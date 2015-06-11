

plot "shutter-clap-laser-0001-first-pulse.data"

g(x) =  A*.25*(1+tanh(a1*(x-x1)))*(1-tanh(a2*(x-x2))) + B

A=-120.
B=5
x1=68000.
x2=85000.
a1=0.1
a2=0.1

fit g(x) "shutter-clap-laser-0001-first-pulse.data" via A,B,a1,a2,x1,x2

set sample 100000
set xlabel "sample"
set ylabel "CLAP gain 1 (ADU)"
set title "CLAP record (gain 1) pulse 0.5s"
plot "shutter-clap-laser-0001-first-pulse.data", g(x)
