# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
This is a problem of building five houses. The masonry, roofing,
painting, etc. must be scheduled. Some tasks must necessarily take
place before others and these requirements are expressed through
precedence constraints.

A pool of two workers is available for building the houses. For a
given house, some tasks (namely: plumbing, ceiling and painting)
require the house to be clean whereas other tasks (namely: masonry,
carpentry, roofing and windows) put the house in a dirty state. A
transition time of 1 is needed to clean the house so to change from
state 'dirty' to state 'clean'.

The objective is to minimize the makespan.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
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

# Number of workers
NB_WORKERS = 2

# Possible states
CLEAN = 0
DIRTY = 1


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

# Initialize model variable sets
all_tasks = []  # Array of all tasks
all_state_functions = []
workers_usage = step_at(0, 0)
desc = dict()
house = dict()

ttime = CpoTransitionMatrix(name='TTime', size=2)
ttime.set_value(DIRTY, CLEAN, 1)

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

    global ttime
    global workers_usage

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

    # TODO:
    # house_state = CpoStateFunction(ttime)
    house_state = state_function(ttime, name="H" + str(loc))
    mdl.add(always_equal(house_state, tasks[MASONRY.id],   DIRTY))
    mdl.add(always_equal(house_state, tasks[CARPENTRY.id], DIRTY))
    mdl.add(always_equal(house_state, tasks[PLUMBING.id],  CLEAN))
    mdl.add(always_equal(house_state, tasks[CEILING.id],   CLEAN))
    mdl.add(always_equal(house_state, tasks[ROOFING.id],   DIRTY))
    mdl.add(always_equal(house_state, tasks[PAINTING.id],  CLEAN))
    mdl.add(always_equal(house_state, tasks[WINDOWS.id],   DIRTY))
    all_state_functions.append(house_state)

    # Allocate tasks to workers
    for t in ALL_TASKS:
        desc[tasks[t.id]] = t
        house[tasks[t.id]] = loc
        workers_usage += pulse(tasks[t.id], 1)


# Make houses
make_house(0, 31)
make_house(1, 0)
make_house(2, 90)
make_house(3, 120)
make_house(4, 90)

# TODO:
# mdl.add(workersUsage <= nbWorkers)
mdl.add(always_in(workers_usage, INTERVAL_MIN, INTERVAL_MAX, 0, NB_WORKERS))

# Add minimization objective
mdl.add(minimize(max([end_of(task) for task in all_tasks])))


##############################################################################
# Solving
##############################################################################

# Trace model
# mdl.export_as_cpo()

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=10000)
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
    workers_function = CpoStepFunction()
    for v in all_tasks:
        itv = msol.get_var_solution(v)
        workers_function.add_value(itv.get_start(), itv.get_end(), 1)

    visu.timeline('Solution SchedState')
    visu.panel(name="Schedule")
    for v in all_tasks:
        visu.interval(msol.get_var_solution(v), house[v], compact(v.get_name()))
    visu.panel(name="Houses state")
    for f in all_state_functions:
        visu.sequence(name=f.get_name(), segments=msol.get_var_solution(f))
    visu.panel(name="Nb of workers")
    visu.function(segments=workers_function, style='line')
    visu.show()
