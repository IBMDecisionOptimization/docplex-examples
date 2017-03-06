# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
This is a problem of building five houses in different locations. The
masonry, roofing, painting, etc. must be scheduled. Some tasks must
necessarily take place before others and these requirements are
expressed through precedence constraints.

There are three workers, and each task requires a worker.  There is
also a cash budget which starts with a given balance.  Each task costs
a given amount of cash per day which must be available at the start of
the task.  A cash payment is received periodically.  The objective is
to minimize the overall completion date.

Please refer to documentation for appropriate setup of solving configuration.
"""


import docplex.cp.utils_visu as visu
from docplex.cp.model import *


##############################################################################
# Model configuration
##############################################################################

# House building task descriptor
class BuildingTask(object):
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

# List of tasks to be executed for each house
MASONRY = BuildingTask('masonry', 35)
CARPENTRY = BuildingTask('carpentry', 15)
PLUMBING = BuildingTask('plumbing', 40)
CEILING = BuildingTask('ceiling', 15)
ROOFING = BuildingTask('roofing', 5)
PAINTING = BuildingTask('painting', 10)
WINDOWS = BuildingTask('windows', 5)
FACADE = BuildingTask('facade', 10)
GARDEN = BuildingTask('garden', 5)
MOVING = BuildingTask('moving', 5)

ALL_TASKS = (MASONRY, CARPENTRY, PLUMBING, CEILING, ROOFING, PAINTING, WINDOWS, FACADE, GARDEN, MOVING)
for i in range(len(ALL_TASKS)):
    ALL_TASKS[i].id = i

NB_WORKERS = 3


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

# Initialize model variable sets
all_tasks = []  # Array of all tasks
cash = step_at(0, 0)
workers_usage = step_at(0, 0)
desc = dict()
house = dict()


# Utility function
def make_house(loc, rd):
    ''' Create model elements corresponding to the building of a house
    loc     Identification of house location
    rd      Min start date
    '''

    # Create interval variable for each task for this house
    tasks = [interval_var(size=t.duration,
                          start=(rd, INTERVAL_MAX),
                          name="H" + str(loc) + "-" + t.name) for t in ALL_TASKS]
    all_tasks.extend(tasks)

    global workers_usage
    global cash

    # Add precedence constraints
    mdl.add(end_before_start(tasks[MASONRY.id], tasks[CARPENTRY.id]))
    mdl.add(end_before_start(tasks[MASONRY.id], tasks[PLUMBING.id]))
    mdl.add(end_before_start(tasks[MASONRY.id], tasks[CEILING.id]))
    mdl.add(end_before_start(tasks[CARPENTRY.id], tasks[ROOFING.id]))
    mdl.add(end_before_start(tasks[CEILING.id], tasks[PAINTING.id]))
    mdl.add(end_before_start(tasks[ROOFING.id], tasks[WINDOWS.id]))
    mdl.add(end_before_start(tasks[ROOFING.id], tasks[FACADE.id]))
    mdl.add(end_before_start(tasks[PLUMBING.id], tasks[FACADE.id]))
    mdl.add(end_before_start(tasks[ROOFING.id], tasks[GARDEN.id]))
    mdl.add(end_before_start(tasks[PLUMBING.id], tasks[GARDEN.id]))
    mdl.add(end_before_start(tasks[WINDOWS.id], tasks[MOVING.id]))
    mdl.add(end_before_start(tasks[FACADE.id], tasks[MOVING.id]))
    mdl.add(end_before_start(tasks[GARDEN.id], tasks[MOVING.id]))
    mdl.add(end_before_start(tasks[PAINTING.id], tasks[MOVING.id]))

    # Allocate tasks to workers
    for t in ALL_TASKS:
        desc[tasks[t.id]] = t
        house[tasks[t.id]] = loc
        workers_usage += pulse(tasks[t.id], 1)
        cash -= step_at_start(tasks[t.id], 200 * t.duration)


# Make houses
make_house(0, 31)
make_house(1, 0)
make_house(2, 90)
make_house(3, 120)
make_house(4, 90)

for p in range(5):
    cash += step_at(60 * p, 30000)

# TODO:
# mdl.add(workers_usage <= NB_WORKERS)
# mdl.add(0 <= cash)

mdl.add(always_in(workers_usage, (INTERVAL_MIN, INTERVAL_MAX), 0, NB_WORKERS))
mdl.add(always_in(cash, (INTERVAL_MIN, INTERVAL_MAX), 0, INT_MAX))

# Add minimization objective
mdl.add(minimize(max([end_of(task) for task in all_tasks])))


##############################################################################
# Solving
##############################################################################

# Trace model
# mdl.export_as_cpo()

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=10000, TimeLimit=10)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

def compact(name):
    # Example: H3-garden -> G3
    #           ^ ^
    loc, task = name[1:].split('-', 1)
    return task[0].upper() + loc

if msol and visu.is_visu_enabled():
    workersF = CpoStepFunction()
    cashF = CpoStepFunction()
    for p in range(5):
        cashF.add_value(60 * p, INT_MAX, 30000)
    for task in all_tasks:
        itv = msol.get_var_solution(task)
        workersF.add_value(itv.get_start(), itv.get_end(), 1)
        cashF.add_value(itv.start, INT_MAX, -200 * desc[task].duration)

    visu.timeline('Solution SchedCumul')
    visu.panel(name="Schedule")
    for task in all_tasks:
        visu.interval(msol.get_var_solution(task), house[task], compact(task.get_name()))
    visu.panel(name="Workers")
    visu.function(segments=workersF, style='area')
    visu.panel(name="Cash")
    visu.function(segments=cashF, style='area', color='gold')
    visu.show()
