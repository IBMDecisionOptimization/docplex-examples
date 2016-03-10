# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
This problem is an extension of the classical Job-Shop Scheduling
problem (see sched_job_shop.py) which allows an operation to be
processed by any machine from a given set. The operation processing
time depends on the allocated machine. The problem is to assign each
operation to a machine and to order the operations on the machines
such that the maximal completion time (makespan) of all operations is
minimized.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
from docplex.cp.model import *


##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(__file__) + "/data/jobshopflex_default.data"

data = []
with open(filename, "r") as file:
    for val in file.read().split():
        data.append(int(val))

nb_jobs = data[0]
nb_mchs = data[1]
ops = []  # An operation is a tuple (id, job id, position in job)
modes = []  # A mode is a tuple (mode id, operation id, job id, machine id, duration)
precs = []  # A precedence is a tuple (operation id, operation id)

p = 2  # Current position in data list
opid = 0
modid = 0
for jobid in range(nb_jobs):
    nbOperations = data[p]
    p += 1
    for j in range(nbOperations):
        nbOpMachines = data[p]
        p += 1
        for k in range(nbOpMachines):
            modes.append((modid, opid, jobid, data[p] - 1, data[p + 1]))
            modid += 1
            p += 2
        ops.append((opid, jobid, j))
        if 0 < j:
            precs.append((opid - 1, opid))
        opid += 1


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

OPS = {o[0]: interval_var(name="O" + str(o[0])) for o in ops}
MODES = {m[0]: interval_var(name="O" + str(m[1]) + "-M" + str(m[0]),
                            optional=True,
                            size=m[4]) for m in modes}
MACHS = [[] for j in range(nb_mchs)]
ALTS = {o[0]: [] for o in ops}
Job = dict()

for m in modes:
    v = MODES[m[0]]
    ALTS[m[1]].append(v)
    MACHS[m[3]].append(v)
    Job[v.get_name()] = m[2]

# Add alternative constraints (machine allocation)
for o in ops:
    mdl.add(alternative(OPS[o[0]], ALTS[o[0]]))

# Add precedence constraints
for p in precs:
    mdl.add(end_before_start(OPS[p[0]], OPS[p[1]]))

# Add no-overlap constraints on each machine
for j in range(nb_mchs):
    mdl.add(no_overlap(MACHS[j]))

# Add minimization objective
mdl.add(minimize(max([end_of(OPS[o[0]]) for o in ops])))


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=100000)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

# Draw solution
if msol and visu.is_visu_enabled():
    visu.timeline("Solution for flexible job-shop " + filename)
    visu.panel("Machines")
    for j in range(nb_mchs):
        visu.sequence(name='M' + str(j))
        for v in MACHS[j]:
            itv = msol.get_var_solution(v)
            if itv.is_present():
                job = Job[v.get_name()]
                visu.interval(itv, job, 'J' + str(job))
    visu.show()
