axe = "z"
pas = "_0.1micron"
dist = "_sur_20micron"
trou = "_20micron"
ext = ".res"

name = axe + pas + dist + trou + ext

r = open(name, mode = "w")

for i in range(O,len(position)):
    m.write(str(position[i]))
    m.write(" ")
    m.write(str(flux))
    m.write(" ")
    m.write(str(flux2))
    m.write("\n")

r.close()
