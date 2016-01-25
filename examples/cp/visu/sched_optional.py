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

There are three workers, and each worker has a given non-negative
skill level for each task.  Each task requires one worker that will
have to be selected among the ones who have a non null skill level for
that task.  A worker can be assigned to only one task at a time.  Each
house has a deadline. The objective is to maximize the skill levels of
the workers assigned to the tasks while respecting the deadlines.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
from docplex.cp.model import *


##############################################################################
# Model configuration
##############################################################################

nbHouses = 5
deadline = 318
workerNames = ['Joe', 'Jack', 'Jim']
nbWorkers = len(workerNames)


# House building task descriptor
class BuildingTask(object):
    def __init__(self, name, duration, skills):
        self.name = name
        self.duration = duration
        self.skills = skills


# List of tasks to be executed for each house
MASONRY = BuildingTask('masonry', 35, [9, 5, 0])
CARPENTRY = BuildingTask('carpentry', 15, [7, 0, 5])
PLUMBING = BuildingTask('plumbing', 40, [0, 7, 0])
CEILING = BuildingTask('ceiling', 15, [5, 8, 0])
ROOFING = BuildingTask('roofing', 5, [6, 7, 0])
PAINTING = BuildingTask('painting', 10, [0, 9, 6])
WINDOWS = BuildingTask('windows', 5, [8, 0, 5])
FACADE = BuildingTask('facade', 10, [5, 5, 0])
GARDEN = BuildingTask('garden', 5, [5, 5, 9])
MOVING = BuildingTask('moving', 5, [6, 0, 8])

ALL_TASKS = (MASONRY, CARPENTRY, PLUMBING, CEILING, ROOFING, PAINTING, WINDOWS, FACADE, GARDEN, MOVING)
for i in range(len(ALL_TASKS)):
    ALL_TASKS[i].id = i


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

# Initialize model variable sets
total_skill = 0
worker_tasks = [[] for w in range(nbWorkers)]  # Tasks assigned to a given worker
desc = dict()


# Utility function
def make_house(loc, deadline):
    ''' Create model elements corresponding to the building of a house
    loc      Identification of house location
    deadline Deadline for finishing the house
    '''

    # Create interval variable for each task for this house
    tasks = [interval_var(size=t.duration,
                          end=(INTERVAL_MIN, deadline),
                          name='H' + str(loc) + '-' + t.name) for t in ALL_TASKS]

    # Add precedence constraints
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

    # Allocate tasks to workers
    global total_skill
    for t in ALL_TASKS:
        allocs = []
        for w in range(nbWorkers):
            if 0 < t.skills[w]:
                wt = interval_var(present=False, name='H' + str(loc) + '-' + t.name + '(' + workerNames[w] + ')')
                worker_tasks[w].append(wt)
                allocs.append(wt)
                total_skill += (t.skills[w] * presence_of(wt))
                desc[wt] = t
        mdl.add(alternative(tasks[t.id], allocs))


# Make houses
for h in range(nbHouses):
    make_house(h, deadline)

# Avoid each worker tasks overlaping
for w in range(nbWorkers):
    mdl.add(no_overlap(worker_tasks[w]))

# Add skill maximization objective
mdl.add(maximize(total_skill))


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

# Draw solution
if msol and visu.is_visu_enabled():
    visu.timeline('Solution SchedOptional', 0, deadline)
    for w in range(nbWorkers):
        visu.sequence(name=workerNames[w])
        for t in worker_tasks[w]:
            wt = msol.get_var_solution(t)
            if wt.is_present():
                if desc[t].skills[w] == max(desc[t].skills):
                    # Green-like color when task is using the most skilled worker
                    color = 'lightgreen'
                else:
                    # Red-like color when task does not use the most skilled worker
                    color = 'salmon'
                visu.interval(wt, color, compact(wt.get_name()))
    visu.show()
