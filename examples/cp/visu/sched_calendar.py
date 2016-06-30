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

There are two workers and each task requires a specific worker.
The worker has a calendar of days off that must be taken into account.
The objective is to minimize the overall completion date.

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import *
import _utils_visu as visu


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

# Tasks assigned to Joe and JIM
JOE_TASKS = (MASONRY, CARPENTRY, ROOFING, FACADE, GARDEN)
JIM_TASKS = (PLUMBING, CEILING, PAINTING, WINDOWS, MOVING)


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

# Initialize model variable sets
all_tasks = []  # Array of all tasks
ends = []  # Array of house finishing times
joe_tasks = []  # Tasks assigned to Joe
jim_tasks = []  # Tasks assigned to Jim
type = dict()

joe_calendar = CpoStepFunction()
jim_calendar = CpoStepFunction()

joe_calendar.set_value(0, 2 * 365, 100)
jim_calendar.set_value(0, 2 * 365, 100)

# Week ends
for w in range(2 * 52):
    joe_calendar.set_value(5 + (7 * w), 7 + (7 * w), 0)
    jim_calendar.set_value(5 + (7 * w), 7 + (7 * w), 0)

# Holidays
joe_calendar.set_value(5, 12, 0)
joe_calendar.set_value(124, 131, 0)
joe_calendar.set_value(215, 236, 0)
joe_calendar.set_value(369, 376, 0)
joe_calendar.set_value(495, 502, 0)
joe_calendar.set_value(579, 600, 0)
jim_calendar.set_value(26, 40, 0)
jim_calendar.set_value(201, 225, 0)
jim_calendar.set_value(306, 313, 0)
jim_calendar.set_value(397, 411, 0)
jim_calendar.set_value(565, 579, 0)


# Utility function
def make_house(loc):
    ''' Create model elements corresponding to the building of a house
    loc     Identification of house
    '''

    # Create interval variable for each task for this house
    tasks = [interval_var(size=t.duration, name="H" + str(loc) + "-" + t.name) for t in ALL_TASKS]
    for t in ALL_TASKS:
        type[tasks[t.id]] = t.id
    for t in JOE_TASKS:
        tasks[t.id].set_intensity(joe_calendar)
        mdl.add(forbid_start(tasks[t.id], joe_calendar))
        mdl.add(forbid_end(tasks[t.id], joe_calendar))
    for t in JIM_TASKS:
        tasks[t.id].set_intensity(jim_calendar)
        mdl.add(forbid_start(tasks[t.id], jim_calendar))
        mdl.add(forbid_end(tasks[t.id], jim_calendar))

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
    for t in JOE_TASKS:
        joe_tasks.append(tasks[t.id])
    for t in JIM_TASKS:
        jim_tasks.append(tasks[t.id])

    # Update cost
    ends.append(end_of(tasks[MOVING.id]))


# Make houses
for i in range(5):
    make_house(i)

# Avoid each worker tasks overlapping
mdl.add(no_overlap(joe_tasks))
mdl.add(no_overlap(jim_tasks))

# Add minimization objective
mdl.add(minimize(max(ends)))


##############################################################################
# Solving
##############################################################################

# Trace model
# mdl.export_as_cpo()

# Solve model
print("Solving model....")
msol = mdl.solve()
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
    visu.timeline('Solution SchedCalendar')
    visu.panel()
    visu.pause(joe_calendar)
    visu.sequence(name='Joe',
                  intervals=[(msol.get_var_solution(t), type[t], compact(t.name)) for t in joe_tasks])
    visu.panel()
    visu.pause(jim_calendar)
    visu.sequence(name='Jim',
                  intervals=[(msol.get_var_solution(t), type[t], compact(t.name)) for t in jim_tasks])
    visu.show()
