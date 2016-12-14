# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
In mathematics, a Golomb ruler is a set of marks at integer positions along
an imaginary ruler such that no two pairs of marks are the same distance apart.
The number of marks on the ruler is its order, and the largest distance
between two of its marks is its length.

This implementation differs from the 'basic' one because it calls the solver
twice:
 * First time to know the minimal size of the ruler for the required order,
 * A second time to list all possible rulers for this optimal size

See https://en.wikipedia.org/wiki/Golomb_ruler for more information.

For order 5: 2 solutions 0 1 4 9 11 ; 0 2 7 8 11   

Please refer to documentation for appropriate setup of solving configuration.
"""


from docplex.cp.model import *
from sys import stdout

# Set model parameters
ORDER = 5        # Number of marks
MAX_LENGTH = 10  # Max rule length, voluntarily TOO SHORT

# Create model
mdl = CpoModel()

# Create array of variables corresponding to position rule marks
marks = integer_var_list(ORDER, 0, MAX_LENGTH, "M")

# Create marks distances that should be all different
dist = [marks[i] - marks[j] for i in range(1, ORDER) for j in range(0, i)]
mdl.add(all_diff(dist))

# Avoid symmetric solutions by ordering marks
mdl.add(marks[0] == 0)
for i in range(1, ORDER):
    mdl.add(marks[i] > marks[i - 1])

# Avoid mirror solution
mdl.add((marks[1] - marks[0]) < (marks[ORDER - 1] - marks[ORDER - 2]))

# Minimize ruler size (position of the last mark)
minexpr = minimize(marks[ORDER - 1])
mdl.add(minexpr)

# First solve the model
solver = CpoSolver(mdl)
msol = solver.solve()
if msol:
    msol.print_solution()
else:
    try:
        rsol = solver.refine_conflict()
        rsol.print_conflict()
    except CpoNotSupportedException:
        print("The configured solver agent does not support conflict refiner.")
