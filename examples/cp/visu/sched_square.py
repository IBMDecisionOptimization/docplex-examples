# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The aim of the square example is to place a set of small squares of
different sizes into a large square.

This version is extended and uses matplotlib to draw the result at the end.
Requires installation of numpy (installer) and following python packages:
    "pip install matplotlib python-dateutil pyparsing"

Please refer to documentation for appropriate setup of solving configuration.
"""

import docplex.cp.utils_visu as visu
from docplex.cp.model import *


##############################################################################
# Model configuration
##############################################################################

# Size of the englobing square
SIZE_SQUARE = 112

# Sizes of the sub-squares
SIZE_SUBSQUARE = [50, 42, 37, 35, 33, 29, 27, 25, 24, 19, 18, 17, 16, 15, 11, 9, 8, 7, 6, 4, 2]


##############################################################################
# Model construction
##############################################################################

# Create model
mdl = CpoModel()

# Create array of variables for subsquares
x = []
y = []
rx = pulse(0, 0, 0)
ry = pulse(0, 0, 0)

for i in range(len(SIZE_SUBSQUARE)):
    sq = SIZE_SUBSQUARE[i]
    vx = interval_var(size=sq, name="X" + str(i))
    vx.set_end((0, SIZE_SQUARE))
    x.append(vx)
    rx += pulse(vx, sq)

    vy = interval_var(size=sq, name="Y" + str(i))
    vy.set_end((0, SIZE_SQUARE))
    y.append(vy)
    ry += pulse(vy, sq)

# Create dependencies between variables
for i in range(len(SIZE_SUBSQUARE)):
    for j in range(i):
        mdl.add((end_of(x[i]) <= start_of(x[j]))
                | (end_of(x[j]) <= start_of(x[i]))
                | (end_of(y[i]) <= start_of(y[j]))
                | (end_of(y[j]) <= start_of(y[i])))

mdl.add(always_in(rx, (0, SIZE_SQUARE), SIZE_SQUARE, SIZE_SQUARE))
mdl.add(always_in(ry, (0, SIZE_SQUARE), SIZE_SQUARE, SIZE_SQUARE))

# Define search phases
mdl.set_search_phases([search_phase(x), search_phase(y)])


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve(TimeLimit=20, LogPeriod=50000)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

if msol and visu.is_visu_enabled():
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from matplotlib.patches import Polygon

    # Plot external square
    print("Plotting squares....")
    fig, ax = plt.subplots()
    plt.plot((0, 0), (0, SIZE_SQUARE), (SIZE_SQUARE, SIZE_SQUARE), (SIZE_SQUARE, 0))
    for i in range(len(SIZE_SUBSQUARE)):
        # Display square i
        (sx, sy) = (msol.get_var_solution(x[i]), msol.get_var_solution(y[i]))
        (sx1, sx2, sy1, sy2) = (sx.get_start(), sx.get_end(), sy.get_start(), sy.get_end())
        poly = Polygon([(sx1, sy1), (sx1, sy2), (sx2, sy2), (sx2, sy1)], fc=cm.Set2(float(i) / len(SIZE_SUBSQUARE)))
        ax.add_patch(poly)
        # Display identifier of square i at its center
        ax.text(float(sx1 + sx2) / 2, float(sy1 + sy2) / 2, str(SIZE_SUBSQUARE[i]), ha='center', va='center')
    plt.margins(0)
    plt.show()
