# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
In the classical Job-Shop Scheduling problem a finite set of jobs is
processed on a finite set of machines. Each job is characterized by a
fixed order of operations, each of which is to be processed on a
specific machine for a specified duration.  Each machine can process
at most one operation at a time and once an operation initiates
processing on a given machine it must complete processing
uninterrupted.  The objective of the problem is to find a schedule
that minimizes the makespan of the schedule.

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import *
import _utils_visu as visu


##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(__file__) + "/data/jobshop_ft06.data"

data = []
with open(filename, "r") as file:
    for val in file.read().split():
        data.append(int(val))

nb_jobs = data[0]
nb_mchs = data[1]
mch = [[data[2 + 2 * (nb_mchs * i + j)] for j in range(nb_mchs)] for i in range(nb_jobs)]
dur = [[data[3 + 2 * (nb_mchs * i + j)] for j in range(nb_mchs)] for i in range(nb_jobs)]


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

ITVS = [[interval_var(size=dur[i][j], name="O" + str(i) + "-" + str(j)) for j in range(nb_mchs)] for i in range(nb_jobs)]
MACH = [[] for j in range(nb_mchs)]

for i in range(nb_jobs):
    for j in range(nb_mchs):
        MACH[mch[i][j]].append(ITVS[i][j])
        if 0 < j:
            mdl.add(end_before_start(ITVS[i][j - 1], ITVS[i][j]))

for j in range(nb_mchs):
    mdl.add(no_overlap(MACH[j]))

# Add minimization objective
mdl.add(minimize(max([end_of(ITVS[i][nb_mchs - 1]) for i in range(nb_jobs)])))


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve()
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

# Draw solution
if msol and visu.is_visu_enabled():
    visu.timeline("Solution for job-shop " + filename)
    visu.panel("Jobs")
    for i in range(nb_jobs):
        visu.sequence(name='J' + str(i),
                      intervals=[(msol.get_var_solution(ITVS[i][j]), mch[i][j], 'M' + str(mch[i][j])) for j in
                                 range(nb_mchs)])
    visu.panel("Machines")
    for k in range(nb_mchs):
        visu.sequence(name='M' + str(k),
                      intervals=[(msol.get_var_solution(MACH[k][i]), k, 'J' + str(i)) for i in range(nb_jobs)])
    visu.show()
