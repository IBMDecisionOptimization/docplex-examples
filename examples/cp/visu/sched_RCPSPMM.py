# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The MMRCPSP (Multi-Mode Resource-Constrained Project Scheduling
Problem) is a generalization of the Resource-Constrained Project
Scheduling problem (see sched_RCPSP.py). In the MMRCPSP, each
activity can be performed in one out of several modes. Each mode of an
activity represents an alternative way of combining different levels
of resource requirements with a related duration. Renewable and
no-renewable resources are distinguished. While renewable resources
have a limited instantaneous availability such as manpower and
machines, non renewable resources are limited for the entire project,
allowing to model, e.g., a budget for the project.  The objective is
to find a mode and a start time for each activity such that the
schedule is makespan minimal and feasible with regard to the
precedence and resource constraints.

Please refer to documentation for appropriate setup of solving configuration.
"""

import docplex.cp.utils_visu as visu
from docplex.cp.model import *

##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(os.path.abspath(__file__)) + "/data/rcpspmm_default.data"

data = []
with open(filename, "r") as file:
    for val in file.read().split():
        data.append(int(val))


class Task(object):
    def __init__(self, name, nb_modes):
        super(Task, self).__init__()
        self._name = name
        self._nb_modes = nb_modes
        self._succs = []
        self._modes = []

    @property
    def name(self):
        return self._name

    @property
    def successors(self):
        return self._succs

    @property
    def nb_modes(self):
        return self._nb_modes

    @property
    def modes(self):
        return self._modes

    def add_successor(self, taskid):
        self._succs.append(taskid)

    def add_mode(self, mode):
        self._modes.append(mode)


class Mode(object):
    def __init__(self, name, task, duration, dem_renewables, dem_non_renewables):
        super(Mode, self).__init__()
        self._name = name
        self._task = task
        self._duration = duration
        self._dem_renewables = dem_renewables
        self._dem_non_renewables = dem_non_renewables

    @property
    def name(self):
        return self._name

    @property
    def task(self):
        return self._task

    @property
    def duration(self):
        return self._duration

    @property
    def demand_renewable(self):
        return self._dem_renewables

    @property
    def demand_non_renewable(self):
        return self._dem_non_renewables


nb_tasks = data[0]
nb_renewable = data[1]
nb_non_renewable = data[2]
p = 3
cap_renewables = data[p:p + nb_renewable]
p += nb_renewable
cap_non_renewables = data[p:p + nb_non_renewable]
p += nb_non_renewable

tasks_data = []
for i in range(nb_tasks):
    p += 1
    task = Task('T' + str(i), data[p])
    p += 1
    ns = data[p]
    p += 1
    for j in range(p, p + ns):
        task.add_successor(data[j])
    p += ns
    tasks_data.append(task)

modes_data = []
for i in range(nb_tasks):
    for j in range(tasks_data[i].nb_modes):
        taskid = data[p]
        p += 1
        modeid = data[p]
        p += 1
        dur = data[p]
        p += 1
        dem_renewables = data[p:p + nb_renewable]
        p += nb_renewable
        dem_non_renewables = data[p:p + nb_non_renewable]
        p += nb_non_renewable
        mode = Mode('T' + str(taskid) + '-M' + str(modeid),
                    tasks_data[i], dur, dem_renewables, dem_non_renewables)
        tasks_data[i].add_mode(mode)
        modes_data.append(mode)


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

tasks = {tasks_data[i]: interval_var(name=tasks_data[i].name) for i in range(nb_tasks)}

modes = {modes_data[i]: interval_var(name=modes_data[i].name,
                                    optional=True,
                                    size=modes_data[i].duration) for i in range(len(modes_data))}

renewables = [pulse(0, 0, 0) for j in range(nb_renewable)]

non_renewables = [0 for j in range(nb_non_renewable)]

# Add precedence constraints
for t in tasks_data:
    for s in t.successors:
        mdl.add(end_before_start(tasks[t], tasks[tasks_data[s]]))

# Add mode allocation constraints
for t in tasks_data:
    mdl.add(alternative(tasks[t], [modes[m] for m in t.modes]))

# Add resource constraints
for m in modes_data:
    for j in range(nb_renewable):
        if 0 < m.demand_renewable[j]:
            renewables[j] += pulse(modes[m], m.demand_renewable[j])
    for j in range(nb_non_renewable):
        if 0 < m.demand_non_renewable[j]:
            non_renewables[j] += m.demand_non_renewable[j] * presence_of(modes[m])

for j in range(nb_renewable):
    # mdl.add(renewables[j]<=capRenewables[j])
    mdl.add(always_in(renewables[j], INTERVAL_MIN, INTERVAL_MAX, 0, cap_renewables[j]))

for j in range(nb_non_renewable):
    mdl.add(non_renewables[j] <= cap_non_renewables[j])

# Add minimization objective
mdl.add(minimize(max([end_of(tasks[t]) for t in tasks_data])))


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=30000, TimeLimit=10)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

if msol and visu.is_visu_enabled():
    load = [CpoStepFunction() for j in range(nb_renewable)]
    for m in modes_data:
        itv = msol.get_var_solution(modes[m])
        if itv.is_present():
            for j in range(nb_renewable):
                if 0 < m.demand_renewable[j]:
                    load[j].add_value(itv.get_start(), itv.get_end(), m.demand_renewable[j])

    visu.timeline("Solution for RCPSPMM " + filename)
    visu.panel("Tasks")
    for t in tasks_data:
        visu.interval(msol.get_var_solution(tasks[t]), int(t.name[1:]), t.name)
    for j in range(nb_renewable):
        visu.panel("R " + str(j + 1))
        visu.function(segments=[(INTERVAL_MIN, INTERVAL_MAX, cap_renewables[j])], style='area', color='lightgrey')
        visu.function(segments=load[j], style='area', color=j)
    visu.show()
