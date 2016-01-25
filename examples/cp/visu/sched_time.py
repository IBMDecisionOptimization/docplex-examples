# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
This is a problem of building a house. The masonry, roofing, painting,
etc. must be scheduled.  Some tasks must necessarily take place before
others and these requirements are expressed through precedence
constraints.

Moreover, there are earliness and tardiness costs associated with some
tasks. The objective is to minimize these costs.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
from docplex.cp.model import *

##############################################################################
# Model configuration
##############################################################################

# Create model
mdl = CpoModel()

# House building task descriptor
class BuildingTask(object):
    def __init__(self, name, duration, release_date=None, due_date=None, earliness_cost=None, tardiness_cost=None):
        self.name = name
        self.duration = duration
        self.release_date = release_date
        self.due_date = due_date
        self.earliness_cost = earliness_cost
        self.tardiness_cost = tardiness_cost

# List of tasks to be executed for the house
MASONRY = BuildingTask('masonry', 35, release_date=25, earliness_cost=200.0)
CARPENTRY = BuildingTask('carpentry', 15, release_date=75, earliness_cost=300.0)
PLUMBING = BuildingTask('plumbing', 40)
CEILING = BuildingTask('ceiling', 15, release_date=75, earliness_cost=100.0)
ROOFING = BuildingTask('roofing', 5)
PAINTING = BuildingTask('painting', 10)
WINDOWS = BuildingTask('windows', 5)
FACADE = BuildingTask('facade', 10)
GARDEN = BuildingTask('garden', 5)
MOVING = BuildingTask('moving', 5, due_date=100, tardiness_cost=400.0)

ALL_TASKS = (MASONRY, CARPENTRY, PLUMBING, CEILING, ROOFING, PAINTING, WINDOWS, FACADE, GARDEN, MOVING)
for i in range(len(ALL_TASKS)):
    ALL_TASKS[i].id = i


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

tasks = [interval_var(size=t.duration, name=t.name) for t in ALL_TASKS]

mdl.add(end_before_start(tasks[MASONRY.id],   tasks[CARPENTRY.id]))
mdl.add(end_before_start(tasks[MASONRY.id],   tasks[PLUMBING.id]))
mdl.add(end_before_start(tasks[MASONRY.id],   tasks[CEILING.id]))
mdl.add(end_before_start(tasks[CARPENTRY.id], tasks[ROOFING.id]))
mdl.add(end_before_start(tasks[CEILING.id],   tasks[PAINTING.id]))
mdl.add(end_before_start(tasks[ROOFING.id],   tasks[WINDOWS.id]))
mdl.add(end_before_start(tasks[ROOFING.id],   tasks[FACADE.id]))
mdl.add(end_before_start(tasks[PLUMBING.id],  tasks[FACADE.id]))
mdl.add(end_before_start(tasks[ROOFING.id],   tasks[GARDEN.id]))
mdl.add(end_before_start(tasks[PLUMBING.id],  tasks[GARDEN.id]))
mdl.add(end_before_start(tasks[WINDOWS.id],   tasks[MOVING.id]))
mdl.add(end_before_start(tasks[FACADE.id],    tasks[MOVING.id]))
mdl.add(end_before_start(tasks[GARDEN.id],    tasks[MOVING.id]))
mdl.add(end_before_start(tasks[PAINTING.id],  tasks[MOVING.id]))

# Cost function
cost = []
fearliness = dict()
ftardiness = dict()

for t in ALL_TASKS:
    task = tasks[t.id]
    if t.release_date is not None:
        f = CpoSegmentedFunction((-t.earliness_cost, 0), [(t.release_date, 0, 0)])
        cost.append(start_eval(task, f))
        fearliness[t] = f
    if t.due_date is not None:
        f = CpoSegmentedFunction((0, 0), [(t.due_date, 0, t.tardiness_cost)])
        cost.append(end_eval(task, f))
        ftardiness[t] = f

# Add minimization objective
mdl.add(minimize(sum(cost)))


##############################################################################
# Solving
##############################################################################

print("Solving model....")
msol = mdl.solve()
print("Solution: ")
msol.print_solution()

##############################################################################
# Display result
##############################################################################

if msol and visu.is_visu_enabled():
    visu.timeline("Solution SchedTime", origin=10, horizon=120)
    visu.panel("Schedule")
    for t in ALL_TASKS:
        visu.interval(msol.get_var_solution(tasks[t.id]), t.id, t.name)
    for t in ALL_TASKS:
        if t.release_date is not None:
            visu.panel('Earliness')
            itvsol = msol.get_var_solution(tasks[t.id])
            cost = fearliness[t].get_value(itvsol.get_start())
            visu.function(segments=[(itvsol, cost, t.name)], color=t.id, style='interval')
            visu.function(segments=fearliness[t], color=t.id)
        if t.due_date is not None:
            visu.panel('Tardiness')
            itvsol = msol.get_var_solution(tasks[t.id])
            cost = ftardiness[t].get_value(itvsol.get_end())
            visu.function(segments=[(itvsol, cost, t.name)], color=t.id, style='interval')
            visu.function(segments=ftardiness[t], color=t.id)
    visu.show()
