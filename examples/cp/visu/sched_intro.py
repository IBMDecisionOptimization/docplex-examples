# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2016
# --------------------------------------------------------------------------

"""
This is a basic problem that involves building a house. The masonry,
roofing, painting, etc.  must be scheduled. Some tasks must
necessarily take place before others, and these requirements are
expressed through precedence constraints.

Please refer to documentation for appropriate setup of solving configuration.
"""

import _utils_visu as visu
from docplex.cp.model import *


##############################################################################
# Modeling
##############################################################################

# Create model
mdl = CpoModel()

masonry   = interval_var(name='masonry',   size=35)
carpentry = interval_var(name='carpentry', size=15)
plumbing  = interval_var(name='plumbing',  size=40)
ceiling   = interval_var(name='ceiling',   size=15)
roofing   = interval_var(name='roofing',   size=5)
painting  = interval_var(name='painting',  size=10)
windows   = interval_var(name='windows',   size=5)
facade    = interval_var(name='facade',    size=10)
garden    = interval_var(name='garden',    size=5)
moving    = interval_var(name='moving',    size=5)

# Add precedence constraints
mdl.add(end_before_start(masonry,   carpentry))
mdl.add(end_before_start(masonry,   plumbing))
mdl.add(end_before_start(masonry,   ceiling))
mdl.add(end_before_start(carpentry, roofing))
mdl.add(end_before_start(ceiling,   painting))
mdl.add(end_before_start(roofing,   windows))
mdl.add(end_before_start(roofing,   facade))
mdl.add(end_before_start(plumbing,  facade))
mdl.add(end_before_start(roofing,   garden))
mdl.add(end_before_start(plumbing,  garden))
mdl.add(end_before_start(windows,   moving))
mdl.add(end_before_start(facade,    moving))
mdl.add(end_before_start(garden,    moving))
mdl.add(end_before_start(painting,  moving))


##############################################################################
# Solving
##############################################################################

# Trace model
if False:
    from CpoCompiler import *
    cplr = CpoCompiler(mdl)
    cplr.set_source_location(False)
    cplr.print_model()

# Solve model
print("Solving model....")
msol = mdl.solve()
print("Solution: ")
msol.print_solution()


##############################################################################
# Display result
##############################################################################

# Draw solution
if msol and visu.is_visu_enabled():
    visu.show(msol)
