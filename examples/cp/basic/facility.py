# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
A company has 10 stores.  Each store must be supplied by one warehouse. The
company has five possible locations where it has property and can build a
supplier warehouse: Bonn, Bordeaux, London, Paris, and Rome. The warehouse
locations have different capacities. A warehouse built in Bordeaux or Rome
could supply only one store. A warehouse built in London could supply two
stores; a warehouse built in Bonn could supply three stores; and a warehouse
built in Paris could supply four stores.

The supply costs vary for each store, depending on which warehouse is the
supplier. For example, a store that is located in Paris would have low supply
costs if it were supplied by a warehouse also in Paris.  That same store would
have much higher supply costs if it were supplied by the other warehouses.

The cost of building a warehouse varies depending on warehouse location.

The problem is to find the most cost-effective solution to this problem, while
making sure that each store is supplied by a warehouse.

Please refer to documentation for appropriate setup of solving configuration.
"""

from docplex.cp.model import *

##############################################################################
## Problem data
##############################################################################

nbLocations = 5
nbStores = 8
capacity = (3, 1, 2, 4, 1)
fixedCost = (480, 200, 320, 340, 300)
cost = ((24, 74, 31, 51, 84),
        (57, 54, 86, 61, 68),
        (57, 67, 29, 91, 71),
        (54, 54, 65, 82, 94),
        (98, 81, 16, 61, 27),
        (13, 92, 34, 94, 87),
        (54, 72, 41, 12, 78),
        (54, 64, 65, 89, 89))


##############################################################################
## Modeling
##############################################################################

# Create CPO model
mdl = CpoModel()

supplier = integer_var_list(nbStores, 0, nbLocations - 1, "supplier")
open = integer_var_list(nbLocations, 0, 1, "open")
      
for s in supplier:
    mdl.add(element(open, s) == 1)

for j in range(nbLocations):
    mdl.add(count(supplier, j) <= capacity[j])    
     
obj = scal_prod(open, fixedCost)
for i in range(nbStores):
    obj = obj + element(supplier[i], cost[i])

# Add minimization objective
mdl.add(minimize(obj))
 

##############################################################################
## Solving
##############################################################################

# Solve model
print("\nSolving model....")
msol = mdl.solve(TimeLimit=10)
msol.print_solution()
