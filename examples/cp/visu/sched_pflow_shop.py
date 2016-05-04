# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The general Flow-Shop scheduling problem is a production problem where
a set of n jobs have to be processed with identical flow pattern on m
machines (see sched_flow_shop.py). In permutation flow-shops the
sequence of jobs is the same on all machines.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
from docplex.cp.model import *


##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(os.path.abspath(__file__)) + "/data/flowshop_default.data"

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

ITVS = [[interval_var(size=dur[i][j], name="O" + str(i) + "-" + str(j)) for j in range(nbMchs)] for i in range(nbJobs)]
SEQS = [sequence_var([ITVS[i][j] for i in range(nbJobs)], name="M" + str(j)) for j in range(nbMchs)]

for i in range(nbJobs):
    for j in range(nbMchs):
        if 0 < j:
            mdl.add(end_before_start(ITVS[i][j - 1], ITVS[i][j]))

for j in range(nbMchs):
    mdl.add(no_overlap(SEQS[j]))
    if 0 < j:
        mdl.add(same_sequence(SEQS[0], SEQS[j]))

# Add minimization objective
mdl.add(minimize(max([end_of(ITVS[i][nbMchs - 1]) for i in range(nbJobs)])))


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
    visu.timeline("Solution for permutation flow-shop " + filename)
    visu.panel("Jobs")
    for i in range(nbJobs):
        visu.sequence(name='J' + str(i),
                      intervals=[(msol.get_var_solution(ITVS[i][j]), j, 'M' + str(j)) for j in range(nbMchs)])
    visu.panel("Machines")
    for j in range(nbMchs):
        visu.sequence(name='M' + str(j),
                      intervals=[(msol.get_var_solution(ITVS[i][j]), j, 'J' + str(i)) for i in range(nbJobs)])
    visu.show()
