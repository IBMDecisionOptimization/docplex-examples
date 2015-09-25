from docplex.mp.model import Model
from docplex.mp.context import DOcloudContext

B = [15, 15, 15]
C = [
    [6, 10, 1],
    [12, 12, 5],
    [15, 4, 3],
    [10, 3, 9],
    [8, 9, 5]
]
A = [
    [5, 7, 2],
    [14, 8, 7],
    [10, 6, 12],
    [8, 4, 15],
    [6, 12, 5]
]


def run_GAP_model(As, Bs, Cs, docloud_context=None):
    mdl = Model('GAP per Wolsey -without- Lagrangian Relaxation', 0, docloud_context=docloud_context)
    print("#As={}, #Bs={}, #Cs={}".format(len(As), len(Bs), len(Cs)))
    number_of_cs = len(C)
    # variables
    x_vars = [mdl.binary_var_list(Cs[i], name=None) for i in range(number_of_cs)]

    # constraints
    for i in range(number_of_cs):
        mdl.add_constraint(mdl.sum(x_vars[i]) <= 1)
        # sum i: a_ij * x_ij <= b[j] for all j
        for j in range(len(B)):
            mdl.add_constraint(mdl.sum(x_vars[i][j] * As[i][j] for i in range(number_of_cs)) <= Bs[j])

    # objective
    total_profit = mdl.sum(mdl.sum(c_ij * x_ij for c_ij, x_ij in zip(c_i, x_i))
                           for c_i, x_i in zip(Cs, x_vars))
    mdl.maximize(total_profit)
    mdl.print_information()
    assert mdl.solve()
    obj = mdl.objective_value
    mdl.print_information()
    print("* GAP with no relaxation run OK, best objective is: {:g}".format(obj))
    mdl.end()
    return obj


def run_GAP_model_with_Lagrangian_relaxation(As, Bs, Cs, max_iters=101, docloud_context=None):
    mdl = Model('GAP per Wolsey -with- Lagrangian Relaxation', 0, docloud_context=docloud_context)
    print("#As={}, #Bs={}, #Cs={}".format(len(As), len(Bs), len(Cs)))
    c_range = range(len(Cs))
    # variables
    x_vars = [mdl.binary_var_list(C[i], name=None) for i in c_range]
    p_vars = [mdl.continuous_var(lb=0) for _ in c_range]  # new for relaxation

    # constraints
    for i in c_range:
        # was  mdl.add_constraint(mdl.sum(xVars[i]) <= 1)
        mdl.add_constraint(mdl.sum(x_vars[i]) == 1 - p_vars[i])
        # sum i: a_ij * x_ij <= b[j] for all j
        for j in range(len(Bs)):
            mdl.add_constraint(mdl.sum(x_vars[i][j] * As[i][j] for i in c_range) <= Bs[j])

    # lagrangian relaxation loop
    eps = 1e-6
    loop_count = 0
    best = 0
    initial_multiplier = 1
    multipliers = [initial_multiplier] * len(Cs)

    total_profit = mdl.sum(mdl.sum(c_ij * x_ij for c_ij, x_ij in zip(c_i, x_i)) for c_i, x_i in zip(Cs, x_vars))
    mdl.add_kpi(total_profit, "Total profit")

    while loop_count <= max_iters:
        loop_count += 1
        # rebuilt at each loop iteration
        total_penalty = mdl.sum(p_vars[i] * multipliers[i] for i in c_range)
        mdl.maximize(total_profit + total_penalty)
        ok = mdl.solve()
        if not ok:
            print("*** solve fails, stopping at iteration: %d" % loop_count)
            break
        best = mdl.objective_value
        penalties = [pv.get_value() for pv in p_vars]
        print('%d> new lagrangian iteration, obj=%g, m=%s, p=%s' % (loop_count, best, str(multipliers), str(penalties)))

        do_stop = True
        justifier = 0
        for k in c_range:
            penalized_violation = penalties[k] * multipliers[k]
            if penalized_violation >= eps:
                do_stop = False
                justifier = penalized_violation
                break

        if do_stop:
            print("* Lagrangian relaxation succeeds, best={:g}, penalty={:g}, #iterations={}"
                  .format(best, total_penalty.get_value(), loop_count))
            break
        else:
            # update multipliers and start loop again.
            scale_factor = 1.0 / float(loop_count)
            multipliers = [max(multipliers[i] - scale_factor * penalties[i], 0.) for i in c_range]
            print('{}> -- loop continues, m={}, justifier={:g}'.format(loop_count, str(multipliers), justifier))

    return best


def run_default_GAP_model_with_lagrangian_relaxation(docloud_context):
    return run_GAP_model_with_Lagrangian_relaxation(As=A, Bs=B, Cs=C, docloud_context=docloud_context)


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

    from docplex.mp.environment import Environment

    env = Environment()
    env.print_information()

    gap_best_obj = run_GAP_model(A, B, C, docloud_context=ctx)
    assert (46 == gap_best_obj)
    relaxed_best = run_GAP_model_with_Lagrangian_relaxation(A, B, C, docloud_context=ctx)
    assert (46 == relaxed_best)
