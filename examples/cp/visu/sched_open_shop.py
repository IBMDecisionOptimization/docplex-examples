# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
This problem can be described as follows: a finite set of operations
has to be processed on a given set of machines. Each operation has a
specific processing time during which it may not be interrupted.
Operations are grouped in jobs, so that each operation belongs to
exactly one job. Furthermore, each operation requires exactly one
machine for processing.

The objective of the problem is to schedule all operations, i.e., to
determine their start time, so as to minimize the maximum completion
time (makespan) given the additional constraints that: operations
which belong to the same job and operations which use the same machine
cannot be processed simultaneously.

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import *
import _utils_visu as visu


##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(__file__) + "/data/openshop_default.data"

data = []
with open(filename, "r") as file:
    for val in file.read().split():
        data.append(int(val))

nbJobs = data[0]
nbMchs = data[1]
dur = [[data[2 + (nbMchs * i + j)] for j in range(nbMchs)] for i in range(nbJobs)]


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

ITVS = [[interval_var(size=dur[i][j], name="J" + str(i) + "-M" + str(j)) for j in range(nbMchs)] for i in range(nbJobs)]

for i in range(nbJobs):
    mdl.add(no_overlap([ITVS[i][j] for j in range(nbMchs)]))

for j in range(nbMchs):
    mdl.add(no_overlap([ITVS[i][j] for i in range(nbJobs)]))

# Add minimization objective
mdl.add(minimize(max([end_of(ITVS[i][j]) for i in range(nbJobs) for j in range(nbMchs)])))


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=10000)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

# Draw solution
if msol and visu.is_visu_enabled():
    visu.timeline("Solution for open-shop " + filename)
    visu.panel("Jobs")
    for i in range(nbJobs):
        visu.sequence(name='J' + str(i),
                      intervals=[(msol.get_var_solution(ITVS[i][j]), j, 'M' + str(j)) for j in range(nbMchs)])
    visu.panel("Machines")
    for j in range(nbMchs):
        visu.sequence(name='M' + str(j),
                      intervals=[(msol.get_var_solution(ITVS[i][j]), j, 'J' + str(i)) for i in range(nbJobs)])
    visu.show()
