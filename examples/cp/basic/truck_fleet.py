# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
The problem is to deliver some orders to several clients with a single truck.
Each order consists of a given quantity of a product of a certain type (called
its color).
The truck must be configured in order to handle one, two or three different colors of products.
The cost for configuring the truck from a configuration A to a configuration B depends on A and B.
The configuration of the truck determines its capacity and its loading cost. 
A truck can only be loaded with orders for the same customer.
Both the cost (for configuring and loading the truck) and the number of travels needed to deliver all the 
orders must be minimized, the cost being the most important criterion. 

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import *
from sys import stdout


##############################################################################
## Problem data
##############################################################################

nbTruckConfigs = 7  # Number of possible configurations for the truck
nbOrders = 21
nbCustomers = 3
nbTrucks = 15  # Max. number of travels of the truck

# Capacity of the trucks
maxTruckConfigLoad = (11, 11, 11, 11, 10, 10, 10)
maxLoad = max(maxTruckConfigLoad)

customerOfOrder = (0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2)
volumes = (3, 4, 3, 2, 5, 4, 11, 4, 5, 2, 4, 7, 3, 5, 2, 5, 6, 11, 1, 6, 3)
colors = (1, 2, 0, 1, 1, 1, 0, 0, 0, 0, 2, 2, 2, 0, 2, 1, 0, 2, 0, 0, 0)

# Cost for loading a truck of a given config         
truckCost = (2, 2, 2, 3, 3, 3, 4)

# Transition costs between trucks
costTuples = tuple_set(((0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 10), (0, 4, 10),
                        (0, 5, 10), (0, 6, 15), (1, 0, 0), (1, 1, 0), (1, 2, 0),
                        (1, 3, 10), (1, 4, 10), (1, 5, 10), (1, 6, 15), (2, 0, 0),
                        (2, 1, 0), (2, 2, 0), (2, 3, 10), (2, 4, 10), (2, 5, 10),
                        (2, 6, 15), (3, 0, 3), (3, 1, 3), (3, 2, 3), (3, 3, 0),
                        (3, 4, 10), (3, 5, 10), (3, 6, 15), (4, 0, 3), (4, 1, 3),
                        (4, 2, 3), (4, 3, 10), (4, 4, 0), (4, 5, 10), (4, 6, 15),
                        (5, 0, 3), (5, 1, 3), (5, 2, 3), (5, 3, 10), (5, 4, 10),
                        (5, 5, 0), (5, 6, 15), (6, 0, 3), (6, 1, 3), (6, 2, 3),
                        (6, 3, 10), (6, 4, 10), (6, 5, 10), (6, 6, 0)
                        ))

##############################################################################
## Modeling
##############################################################################

# Create CPO model
mdl = CpoModel()

# Configuration of the truck
truckConfigs = integer_var_list(nbTrucks, 0, nbTruckConfigs - 1, "truckConfigs")
# In which truck is an order
where = integer_var_list(nbOrders, 0, nbTrucks - 1, "where")
# Load of a truck
load = integer_var_list(nbTrucks, 0, maxLoad, "load")
# Number of trucks used
numUsed = integer_var(0, nbTrucks)
#
customerOfTruck = integer_var_list(nbTrucks, 0, nbCustomers, "customerOfTruck")
#
transitionCost = integer_var_list(nbTrucks - 1, 0, 1000, "transitionCost")

for i in range(1, nbTrucks):
    auxVars = (truckConfigs[i - 1], truckConfigs[i], transitionCost[i - 1])
    mdl.add(allowed_assignments(auxVars, costTuples))

# Constrain the volume of the orders in each truck 
mdl.add(pack(load, where, volumes, numUsed))
for i in range(0, nbTrucks):
    mdl.add(load[i] <= element(truckConfigs[i], maxTruckConfigLoad))

# Compatibility between the colors of an order and the configuration of its truck 
allowedContainerConfigs = ((0, 3, 4, 6),
                           (1, 3, 5, 6),
                           (2, 4, 5, 6))
for j in range(0, nbOrders):
    configOfContainer = integer_var(allowedContainerConfigs[colors[j]])
    mdl.add(configOfContainer == element(where[j], truckConfigs))

# Only one customer per truck 
for j in range(0, nbOrders):
    mdl.add(element(where[j], customerOfTruck) == customerOfOrder[j])

# Non-used trucks are at the end
for j in range(1, nbTrucks):
    mdl.add((load[j - 1] > 0) | (load[j] == 0))

# Dominance: the non used trucks keep the last used configuration
mdl.add(load[0] > 0)
for i in range(1, nbTrucks):
    mdl.add((load[i] > 0) | (truckConfigs[i] == truckConfigs[i - 1]))

# Dominance: regroup deliveries with same configuration
for i in range(nbTrucks - 2, 0, -1):
    ct = true()
    for p in range(i + 1, nbTrucks):
        ct = (truckConfigs[p] != truckConfigs[i - 1]) & ct
    mdl.add((truckConfigs[i] == truckConfigs[i - 1]) | ct)

# Objective: first criterion for minimizing the cost for configuring and loading trucks 
#            second criterion for minimizing the number of trucks
obj1 = 0
for i in range(nbTrucks):
    obj1 = obj1 + element(truckConfigs[i], truckCost) * (load[i] != 0)
obj1 = obj1 + sum(transitionCost)

obj2 = numUsed

# Search strategy: first assign order to truck
mdl.set_search_phases([search_phase(where)])

# Multicriteria lexicographic optimization
mdl.add(minimize_static_lex([obj1, obj2]))


##############################################################################
## Solving
##############################################################################

# Solve model
print("\nSolving model....")
msol = mdl.solve(TimeLimit=30, LogPeriod=3000)

# Print solution
if msol.is_solution():
    print("Solution: ")
    ovals = msol.get_objective_values()
    print("   Configuration cost: " + str(ovals[0]))
    print("   Number of Trucks:   " + str(ovals[1]))
    for i in range(nbTrucks):
        ld = msol.get_value(load[i])
        if ld > 0:
            stdout.write("Truck " + str(i)
                         + ": config=" + str(msol.get_value(truckConfigs[i]))
                         + ", items=")
            for j in range(nbOrders):
                if (msol.get_value(where[j]) == i):
                    stdout.write("<" + str(j) + "," + str(colors[j]) + "," + str(volumes[j]) + "> ")
            stdout.write('\n')
else:
    stdout.write("Solve status: " + msol.get_solve_status() + "\n")
