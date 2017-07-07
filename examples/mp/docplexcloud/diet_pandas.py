# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2015, 2017
# --------------------------------------------------------------------------

# The goal of the diet problem is to select a set of foods that satisfies
# a set of daily nutritional requirements at minimal cost.
# Source of data: http://www.neos-guide.org/content/diet-problem-solver

import os
from os.path import splitext

import pandas

from six import iteritems

from docplex.mp.model import Model
from docplex.util.environment import get_environment


def get_all_inputs():
    '''Utility method to read a list of files and return a tuple with all
    read data frames.

    Returns:
        a map { datasetname: data frame }
    '''
    result = {}
    env = get_environment()
    for iname in [f for f in os.listdir('.') if splitext(f)[1] == '.csv']:
        with env.get_input_stream(iname) as in_stream:
            df = pandas.read_csv(in_stream)
            datasetname, _ = splitext(iname)
            result[datasetname] = df
    return result


def write_all_outputs(outputs):
    '''Write all dataframes in ``outputs`` as .csv.

    Args:
        outputs: The map of outputs 'outputname' -> 'output df'
    '''
    for (name, df) in iteritems(outputs):
        csv_file = '%s.csv' % name
        with get_environment().get_output_stream(csv_file) as fp:
            fp.write(df.to_csv(index=False))


def mp_solution_to_df(solution):
    solution_df = pandas.DataFrame(columns=['name', 'value'])

    for index, dvar in enumerate(solution.iter_variables()):
        solution_df.loc[index, 'name'] = dvar.to_string()
        solution_df.loc[index, 'value'] = dvar.solution_value

    return solution_df


def build_diet_model(inputs, **kwargs):
    '''Constructs a diet model.

    Args:
        inputs: map with inputs { 'datasetname': df }
        **kwargs: kwargs passed to the docplex.mp.model.Model constructor.
    '''
    food = inputs['diet_food']
    nutrients = inputs['diet_nutrients']
    food_nutrients = inputs['diet_food_nutrients']
    food_nutrients.set_index('Food', inplace=True)

    # Model
    mdl = Model(name='diet', **kwargs)

    # Create decision variables, limited to be >= Food.qmin and <= Food.qmax
    qty = food[['name', 'qmin', 'qmax']].copy()
    qty['var'] = qty.apply(lambda x: mdl.continuous_var(lb=x['qmin'],
                                                        ub=x['qmax'],
                                                        name=x['name']),
                           axis=1)
    # make the name the index
    qty.set_index('name', inplace=True)

    # Limit range of nutrients, and mark them as KPIs
    for n in nutrients.itertuples():
        amount = mdl.sum(qty.loc[f.name]['var'] * food_nutrients.loc[f.name][n.name]
                         for f in food.itertuples())
        mdl.add_range(n.qmin, amount, n.qmax)
        mdl.add_kpi(amount, publish_name='Total %s' % n.name)

    # Minimize cost
    mdl.minimize(mdl.sum(qty.loc[f.name]['var'] * f.unit_cost
                         for f in food.itertuples()))

    mdl.print_information()
    return mdl


if __name__ == '__main__':
    '''Build and solve the diet model.

    This sample was build to run on DOcplexcloud solve service.
    '''
    inputs = get_all_inputs()

    mdl = build_diet_model(inputs)

    mdl.float_precision = 3
    if not mdl.solve():
        print('*** Problem has no solution')
    else:
        print('* model solved as function:')
        mdl.print_solution()
        mdl.report_kpis()
        # Save the CPLEX solution as 'solution.csv' program output
        solution_df = mp_solution_to_df(mdl.solution)

        outputs = {'solution': solution_df}

        write_all_outputs(outputs)
