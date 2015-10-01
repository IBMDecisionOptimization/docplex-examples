from collections import namedtuple

from docplex.mp.model import Model
from docplex.mp.context import DOcloudContext

nbs = (8, 1, 1, 16)

team_div1 = {"Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns",
             "Pittsburgh Steelers", "Houston Texans", "Indianapolis Colts",
             "Jacksonville Jaguars", "Tennessee Titans", "Buffalo Bills",
             "Miami Dolphins", "New England Patriots", "New York Jets",
             "Denver Broncos", "Kansas City Chiefs", "Oakland Raiders",
             "San Diego Chargers"}

team_div2 = {"Chicago Bears", "Detroit Lions", "Green Bay Packers",
             "Minnesota Vikings", "Atlanta Falcons", "Carolina Panthers",
             "New Orleans Saints", "Tampa Bay Buccaneers", "Dallas Cowboys",
             "New York Giants", "Philadelphia Eagles", "Washington Redskins",
             "Arizona Cardinals", "San Francisco 49ers", "Seattle Seahawks",
             "St. Louis Rams"}

Match = namedtuple("Matches", ["team1", "team2", "is_divisional"])


def build_sports(docloud_context=None):
    print("* building sport scheduling model instance")
    model = Model('sportSchedCPLEX', docloud_context=docloud_context)

    nb_teams_in_division = nbs[0]
    nb_intra_divisional = nbs[1]
    nb_inter_divisional = nbs[2]
    assert len(team_div1) == len(team_div2)
    model.teams = list(team_div1 | team_div2)
    # team index ranges from 1 to 2N
    team_range = range(1, 2 * nb_teams_in_division + 1)

    # Calculate the number of weeks necessary.
    nb_weeks = (nb_teams_in_division - 1) * nb_intra_divisional + nb_teams_in_division * nb_inter_divisional
    weeks = range(1, nb_weeks + 1)
    model.weeks = weeks

    print("{0} games, {1} intradivisional, {2} interdivisional"
          .format(nb_weeks, (nb_teams_in_division - 1) * nb_intra_divisional,
                  nb_teams_in_division * nb_inter_divisional))

    # Season is split into two halves.
    first_half_weeks = range(1, nb_weeks // 2 + 1)
    nb_first_half_games = nb_weeks // 3

    # All possible matches (pairings) and whether of not each is intradivisional.
    matches = [Match(t1, t2, 1 if (t2 <= nb_teams_in_division or t1 > nb_teams_in_division) else 0)
               for t1 in team_range for t2 in team_range if t1 < t2]
    model.matches = matches
    # Number of games to play between pairs depends on
    # whether the pairing is intradivisional or not.
    nb_play = {m: nb_intra_divisional if m.is_divisional == 1 else nb_inter_divisional for m in matches}

    plays = model.binary_var_matrix(keys1=matches, keys2=weeks,
                                    name=lambda mw: "play_%d_%d_w%d" % (mw[0].team1, mw[0].team2, mw[1]))
    model.plays = plays

    for m in matches:
        model.add_constraint(model.sum(plays[m, w] for w in weeks) == nb_play[m],
                             "correct_nb_games_%d_%d" % (m.team1, m.team2))

    for w in weeks:
        # Each team must play exactly once in a week.
        for t in team_range:
            max_teams_in_division = (plays[m, w] for m in matches if m.team1 == t or m.team2 == t)
            model.add_constraint(model.sum(max_teams_in_division) == 1,
                                 "plays_exactly_once_%d_%s" % (w, t))

        # Games between the same teams cannot be on successive weeks.
        for m in matches:
            if w < nb_weeks:
                model.add_constraint(plays[m, w] + plays[m, w + 1] <= 1)

    # Some intradivisional games should be in the first half.
    for t in team_range:
        max_teams_in_division = [plays[m, w] for w in first_half_weeks for m in matches if
                                 m.is_divisional == 1 and (m.team1 == t or m.team2 == t)]

        model.add_constraint(model.sum(max_teams_in_division) >= nb_first_half_games,
                             "in_division_first_half_%s" % t)

    # postpone divisional matches as much as possible
    # we weight each play variable with the square of w.
    model.maximize(model.sum(plays[m, w] * w * w for w in weeks for m in matches if m.is_divisional))
    return model


def solve_sports(docloud_context=None):
    model = build_sports(docloud_context=docloud_context)
    model.print_information()
    model.export_as_lp()
    model.solve()
    model.report()
    TSolution = namedtuple("TSolution", ["week", "is_divisional", "team1", "team2"])

    # iterate with weeks first
    solution = [TSolution(w, m.is_divisional, model.teams[m.team1], model.teams[m.team2])
                for w in model.weeks for m in model.matches
                if model.plays[m, w].to_bool()]

    currweek = 0
    print("Intradivisional games are marked with a *")
    for s in solution:
        # assume records are sorted by increasing week indices.
        if s.week != currweek:
            currweek = s.week
            print(" == == == == == == == == == == == == == == == == ")
            print("On week %d" % currweek)

        print("    {0:s}{1} will meet the {2}".format("*" if s.is_divisional else "", s.team1, s.team2))
    return model.objective_value


if __name__ == '__main__':
    """DOcloud credentials can be specified here with url and api_key in the code block below.

    Alternatively, if api_key is None, DOcloudContext.make_default_context()
    looks for a .docplexrc file in your home directory on unix ($HOME)
    or user profile directory on windows (%UserProfile%). That file contains the
    credential and other properties. For example, something similar to::

       url = "https://docloud.service.com/job_manager/rest/v1"
       api_key = "example api_key"
    """
    print("This example hits the limits of CPLEX Optimization Studio and will work only the DOcloud solve.")
    url = "YOUR_URL_HERE"
    api_key = None
    ctx = DOcloudContext.make_default_context(url, api_key)
    ctx.print_information()

    from docplex.mp.environment import Environment

    env = Environment()
    env.print_information()

    solve_sports(docloud_context=ctx)
