
import lsst.testbench

B = lsst.testbench.Bench()

print(dir(B))

B.register("laser", "laser")

