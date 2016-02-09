# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The eight queens puzzle is the problem of placing eight chess queens on an 8x8
chessboard so that no two queens threaten each other. Thus, a solution requires
that no two queens share the same row, column, or diagonal.

The eight queens puzzle is an example of the more general n-queens problem of
placing n queens on an nxn chessboard, where solutions exist for all natural
numbers n with the exception of n=2 and n=3.

See https://en.wikipedia.org/wiki/Eight_queens_puzzle for more information.

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import *
from sys import stdout

# Set model parameters
NB_QUEEN = 8

# Create model
mdl = CpoModel()

# Create column index of each queen
x = integer_var_list(NB_QUEEN, 0, NB_QUEEN - 1, "X")

# One queen per raw
mdl.add(all_diff(x))

# One queen per diagonal xi - xj != i - j
mdl.add(all_diff(x[i] + i for i in range(NB_QUEEN)))

# One queen per diagonal xi - xj != j - i
mdl.add(all_diff(x[i] - i for i in range(NB_QUEEN)))
    
# Solve model
print("Solving model....")
msol = mdl.solve()

# Print solution
if msol:
    stdout.write("Solution:")
    for v in x:
        stdout.write(" " + str(msol[v]))
    stdout.write("\n")
else:
    stdout.write("Solve status: " + msol.get_solve_status() + "\n")
