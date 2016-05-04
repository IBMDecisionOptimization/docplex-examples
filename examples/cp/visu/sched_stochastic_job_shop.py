# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
Problem Description
-------------------

The Stochastic Job-Shop Scheduling problem is a variant of the classical
deterministic Job-Shop Scheduling problem (see sched_jobshop.cpp) where
the duration of operations is uncertain.

Scenarios
---------

This example illustrates how to solve a Stochastic Job-Shop Scheduling
problem using a scenario-based approach. A set of n scenarios is created,
each scenario represents a particular realization of the durations of
the operations.

The instance is a small 6x6 Job-Shop Scheduling problem with 20 scenarios.
In the example we suppose the scenarios are given as input. In practical
problems, these scenarios may be given by a selection of representative
past execution of the system or they may be computed by sampling the
probability distributions of operations duration.

For example the different scenarios give the following durations
for the 6 operations of the first job:

JOB #1
                 Machine:  M5 -> M1 -> M4 -> M3 -> M0 -> M2
Duration in scenario #00: 218  284  321  201  101  199
Duration in scenario #01: 259  313  311  191   93  211
...
Duration in scenario #19: 501  309  301  203   95  213

The objective is to find a robust sequencing of operations on machines so
as to minimize the expected makespan across all scenarios.

The problem can be seen as a particular case of Two-Stage Stochastic
Programming problem where first stage decision variables are the sequences
of operations on machines and second stage decision variables are the
actual start/end time of operations that will depend on the actual duration
of operations at execution time.

The model proposed here generalizes to any type of stochastic scheduling
problem where first stage decision variables involve creating robust
sequences of operations on a machine.

Model
-----

Each scenario is modeled as a particular deterministic Job-Shop Scheduling
problem.

Let makespan[k] denote the makespan of scenario k and sequence[k][j] denote
the sequence variable representing the sequencing of operations on machine
j in scenario k.

A set of 'sameSequence' constraints are posted across all scenarios k to
state that for a machine j, the sequence of operations should be the same
for all scenarios. The sequence variable of the first scenario (sequence[0][j])
is used as reference:
for j, for 0<k: sameSequence(sequence[0][j],sequence[k][j])

The global objective function is the average makespan over the different
scenarios:
objective: (sum(k) makespan[k]) / nbScenarios

Solution quality
----------------

Solution with expected makespan 4648.4 is in fact optimal.

Note that the solution built by using the optimal solution of the
deterministic Job-Shop Scheduling problem using average operation duration
yields an expected makespan of 4749.6 which is clearly suboptimal.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
from docplex.cp.model import *

##############################################################################
# Reading instance file
##############################################################################

filename = os.path.dirname(os.path.abspath(__file__)) + "/data/stochastic_jobshop_default.data"

data = []
with open(filename, "r") as file:
    for val in file.read().split():
        data.append(int(val))

nb_jobs = data[0]
nb_machines = data[1]
nb_scenarios = data[2]
p = 3
machines = [[data[p + (nb_machines * i) + j] for j in range(nb_machines)] for i in range(nb_jobs)]
p += nb_machines * nb_jobs
durations = [[[data[p + nb_machines * (nb_jobs * k + i) + j] for j in range(nb_machines)] for i in range(nb_jobs)] for k
             in range(nb_scenarios)]


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

# Build sub-model corresponding to the kth scenario
def make_scenario_submodel(k):
    itvs = [[interval_var(size=durations[k][i][j],
                          name='O' + str(k) + '-' + str(i) + '-' + str(j)) for j in range(nb_machines)] for i in
            range(nb_jobs)]
    mach = [[]] * nb_machines

    for i in range(nb_jobs):
        for j in range(nb_machines):
            mach[machines[i][j]].append(itvs[i][j])
            if 0 < j:
                mdl.add(end_before_start(itvs[i][j - 1], itvs[i][j]))

    sequences = [sequence_var(mach[j], name='S' + str(k) + ':M' + str(j)) for j in range(nb_machines)]
    for s in sequences:
        mdl.add(no_overlap(s))
    makespan = integer_var(0, INT_MAX, name='makespan' + str(k))
    mdl.add(makespan == max([end_of(itvs[i][nb_machines - 1]) for i in range(nb_jobs)]))
    return sequences, makespan

ref_sequences = []
makespans = []

for k in range(nb_scenarios):
    sequences, makespan = make_scenario_submodel(k)
    makespans.append(makespan)
    if k == 0:
        ref_sequences = sequences
    else:
        for j in range(nb_machines):
            mdl.add(same_sequence(ref_sequences[j], sequences[j]))

expected_makespan = sum(makespans) / nb_scenarios

mdl.add(minimize(expected_makespan))


##############################################################################
# Model solving
##############################################################################

# Solve model
print("Solving model....")
msol = mdl.solve(FailLimit=250000)
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

if msol and visu.is_visu_enabled():
    import _utils_visu as visu
    import matplotlib.pyplot as plt

    makespan_values = [msol.get_var_solution(m).get_value() for m in makespans]
    plt.hist(makespan_values, color='skyblue')
    plt.axvline(msol.get_objective_values()[0], color='navy', linestyle='dashed', linewidth=2)
    plt.title("Makespan histogram")
    plt.xlabel("Value")
    plt.ylabel("Frequency")

    visu.timeline("Solution sequencing for stochastic job-shop " + filename)
    visu.panel("Machines")
    for j in range(nb_machines):
        visu.sequence(name='M' + str(j))
        itvs = msol.get_var_solution(ref_sequences[j]).get_value()
        for v in itvs:
            k, i, m = v.get_name().split('-')
            visu.interval(v, int(i), 'O' + i + '-' + m)
    visu.show()
