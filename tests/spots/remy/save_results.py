
direc = "./results/"
axe = "z"
pas = "_0.1micron"
dist = "_sur_20micron"
trou = "_20micron"
ext = ".res"

name = direc + axe + pas + dist + trou + ext

r = open(name, mode = "w")

for i in range(0,len(position)):
    r.write(str(position[i]))
    r.write(" ")
    r.write(str(flux[i]))
    r.write(" ")
    r.write(str(flux2[i]))
    r.write("\n")

r.close()
