"""The model aims at minimizing the production cost for a number of products while satisfying customer demand.
Each product can be produced either inside the company or outside, at a higher cost.
The inside production is constrained by the company's resources, while outside production is considered unlimited.
The model first declares the products and the resources.
The data consists of the description of the products (the demand, the inside and outside costs,
and the resource consumption) and the capacity of the various resources.
The variables for this problem are the inside and outside production for each product.
"""

from docplex.mp.model import Model
from docplex.mp.context import DOcloudContext


def build_production_problem(products, resources, consumptions, docloud_context=None):
    """ Takes as input:
        - a list of product tuples (name, demand, inside, outside)
        - a list of resource tuples (name, capacity)
        - a list of consumption tuples (product_name, resource_named, consumed)
    """
    mdl = Model('production', docloud_context=docloud_context)
    # --- decision variables ---
    mdl.inside_vars = mdl.continuous_var_dict(products, name='inside')
    mdl.outside_vars = mdl.continuous_var_dict(products, name='outside')

    # --- constraints ---
    # demand satisfaction
    for prod in products:
        mdl.add_constraint(mdl.inside_vars[prod] + mdl.outside_vars[prod] >= prod[1])

    # --- resource capacity ---
    for res in resources:
        mdl.add_constraint(mdl.sum([mdl.inside_vars[p] * consumptions[p[0], res[0]] for p in products]) <= res[1])

    # --- objective ---
    mdl.total_inside_cost = mdl.sum(mdl.inside_vars[p] * p[2] for p in products)
    mdl.total_outside_cost = mdl.sum(mdl.outside_vars[p] * p[3] for p in products)
    mdl.minimize(mdl.total_inside_cost + mdl.total_outside_cost)
    return mdl


def solve_production_problem(products, resources, consumptions, docloud_context=None):
    mdl = build_production_problem(products, resources, consumptions, docloud_context)
    # --- solve ---
    mdl.print_information()
    if not mdl.solve():
        print("Problem has no solution")
        return -1

    obj = mdl.objective_value
    print("* Production model solved with objective: {:g}".format(obj))
    print("* Total inside cost=%g" % mdl.total_inside_cost.solution_value)
    for p in products:
        print("Inside production of {product}: {ins_var}".format
              (product=p[0], ins_var=mdl.inside_vars[p].solution_value))
    print("* Total outside cost=%g" % mdl.total_outside_cost.solution_value)
    for p in products:
        print("Outside production of {product}: {out_var}".format
              (product=p[0], out_var=mdl.outside_vars[p].solution_value))
    return obj


PRODUCTS = [("kluski", 100, 0.6, 0.8),
            ("capellini", 200, 0.8, 0.9),
            ("fettucine", 300, 0.3, 0.4)]

# resources are a list of simple tuples (name, capacity)
RESOURCES = [("flour", 20),
             ("eggs", 40)]

CONSUMPTIONS = {("kluski", "flour"): 0.5,
                ("kluski", "eggs"): 0.2,
                ("capellini", "flour"): 0.4,
                ("capellini", "eggs"): 0.4,
                ("fettucine", "flour"): 0.3,
                ("fettucine", "eggs"): 0.6}

if __name__ == '__main__':
    """DOcloud credentials can be specified here with url and api_key in the code block below.
    
    Alternatively, if api_key is None, DOcloudContext.make_default_context()
    looks for a .docplexrc file in your home directory on unix ($HOME)
    or user profile directory on windows (%UserProfile%). That file contains the
    credential and other properties. For example, something similar to::
    
       url = "https://docloud.service.com/job_manager/rest/v1"
       api_key = "example api_key"
    """

    url = "YOUR_URL_HERE"
    api_key = None
    ctx = DOcloudContext.make_default_context(url, api_key)
    ctx.print_information()

    EXPECTED_COST = 372
    print("* Running production model as a function")
    fobj = solve_production_problem(PRODUCTS, RESOURCES, CONSUMPTIONS, docloud_context=ctx)
    assert fobj == EXPECTED_COST
