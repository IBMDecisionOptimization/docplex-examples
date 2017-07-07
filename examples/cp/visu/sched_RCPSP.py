# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The RCPSP (Resource-Constrained Project Scheduling Problem) is a
generalization of the production-specific Job-Shop (see
sched_job_shop.py), Flow-Shop (see sched_flow_shop.py) and Open-Shop
(see sched_open_shop.py) scheduling problems.

Given:
- a set of q resources with given capacities,
- a network of precedence constraints between the activities, and
- for each activity and each resource the amount of the resource
  required by the activity over its execution,
the goal of the RCPSP is to find a schedule meeting all the
constraints whose makespan (i.e., the time at which all activities are
finished) is minimal.

Please refer to documentation for appropriate setup of solving configuration.
"""

import docplex.cp.utils_visu as visu
from docplex.cp.model import *

##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(os.path.abspath(__file__)) + "/data/rcpsp_default.data"

data = []
with open(filename, "r") as file:
    for val in file.read().split():
        data.append(int(val))

nbTasks = data[0]
nbResources = data[1]
capacities = data[2:2 + nbResources]
durations = [0 for i in range(nbTasks)]
successors = [[] for i in range(nbTasks)]
demands = [[] for i in range(nbTasks)]
p = 2 + nbResources  # Current position in data list
for i in range(nbTasks):
    durations[i] = data[p]
    p += 1
    demands[i] = data[p:p + nbResources]
    p += nbResources
    ns = data[p]
    p += 1
    successors[i] = data[p:p + ns]
    p += ns


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

# Create task interval variables
tasks = [interval_var(name='T' + str(i + 1), size=durations[i]) for i in range(nbTasks)]

# Add precedence constraints
for i in range(nbTasks):
    for s in successors[i]:
        mdl.add(end_before_start(tasks[i], tasks[s - 1]))

# Add resource constraints
for j in range(nbResources):
    resources = [pulse(tasks[i], demands[i][j]) for i in range(nbTasks) if demands[i][j] > 0]
    mdl.add(mdl.sum(resources) <= capacities[j])


# Add minimization objective
mdl.add(minimize(max([end_of(tasks[i]) for i in range(nbTasks)])))


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=100000, TimeLimit=10)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

if msol and visu.is_visu_enabled():
    load = [CpoStepFunction() for j in range(nbResources)]
    for i in range(nbTasks):
        itv = msol.get_var_solution(tasks[i])
        for j in range(nbResources):
            if 0 < demands[i][j]:
                load[j].add_value(itv.get_start(), itv.get_end(), demands[i][j])

    visu.timeline("Solution for RCPSP " + filename)
    visu.panel("Tasks")
    for i in range(nbTasks):
        visu.interval(msol.get_var_solution(tasks[i]), i, tasks[i].get_name())
    for j in range(nbResources):
        visu.panel("R " + str(j + 1))
        visu.function(segments=[(INTERVAL_MIN, INTERVAL_MAX, capacities[j])], style='area', color='lightgrey')
        visu.function(segments=load[j], style='area', color=j)
    visu.show()
