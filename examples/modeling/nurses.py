from collections import namedtuple

from enum import Enum

from docplex.mp.model import Model
from docplex.mp.context import DOcloudContext


class Weekday(Enum):
    (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday) = range(1, 8)  # [1..7]


TWorkRules = namedtuple("TWorkRules", ["work_time_max"])
TShift1 = namedtuple("TShift", ["department", "day", "start_time", "end_time", "min_requirement", "max_requirement"])
TVacation = namedtuple("TVacation", ["nurse", "day"])
TNursePair = namedtuple("TNursePair", ["firstNurse", "secondNurse"])
TSkillRequirement = namedtuple("TSkillRequirement", ["department", "skill", "required"])


# subclass the namedtuple to refine the str() method as the nurse's name
class TNurse(namedtuple("TNurse1", ["name", "seniority", "qualification", "payRate"])):
    def __str__(self):
        return self.name


# specialized namedtuple to redefine its str() method
class TShift(TShift1):
    def __str__(self):
        # keep first two characters in department, uppercase
        dept2 = self.department[0:4].upper()
        # keep 3 days of weekday
        dayname = self.day.name[0:3]
        return '{}_{}_{:02d}'.format(dept2, dayname, self.start_time)


class ShiftActivity(object):
    @staticmethod
    def to_abstime(day_index, time_of_day):
        """ Convert a pair (day_index, time) into a number of hours since Monday 00:00

        :param day_index: The index of the day from 1 to 7 (Monday is 1).
        :param time_of_day: An integer number of hours.

        :return:
        """
        ONE_DAY = 24
        time = ONE_DAY * (day_index - 1)
        time += time_of_day
        return time

    def __init__(self, weekday, start_time_of_day, end_time_of_day):
        assert (isinstance(weekday, Weekday))
        assert (start_time_of_day >= 0)
        assert (start_time_of_day <= 24)
        assert (end_time_of_day >= 0)
        assert (end_time_of_day <= 24)

        self._weekday = weekday
        self._start_time_of_day = start_time_of_day
        self._end_time_of_day = end_time_of_day
        # conversion to absolute time.
        start_day_index = weekday.value
        self.start_time = self.to_abstime(start_day_index, start_time_of_day)
        end_day_index = start_day_index if end_time_of_day > start_time_of_day else start_day_index + 1
        self.end_time = self.to_abstime(end_day_index, end_time_of_day)
        assert (self.end_time > self.start_time)

    @property
    def duration(self):
        return self.end_time - self.start_time

    def overlaps(self, other_shift):
        if not isinstance(other_shift, ShiftActivity):
            return False
        else:
            return other_shift.end_time > self.start_time and other_shift.start_time < self.end_time


def solve(model):
    if model.solve():
        print("solution for a cost of {}".format(model.objective_value))
        print_information(model)
        print_solution(model)
        return model.objective_value
    else:
        print("* model is infeasible")
        return None


def load_data(model, *args):
    """ Usage: load_data(departments, skills, shifts, nurses, nurse_skills, vacations) """
    model.number_of_overlaps = 0
    model.work_rules = DEFAULT_WORK_RULES
    number_of_args = len(args)
    model.departments = args[0]
    model.skills = args[1]
    model.shifts = [TShift(*shift_row) for shift_row in args[2]]
    model.nurses = [TNurse(*nurse_row) for nurse_row in args[3]]
    model.nurse_skills = args[4]
    model.skill_requirements = SKILL_REQUIREMENTS
    # transactional data
    if number_of_args >= 6:
        model.vacations = [TVacation._make(vacation_row) for vacation_row in args[5]]
    else:
        model.vacations = []
    if number_of_args >= 7:
        model.nurse_associations = [TNursePair._make(npr) for npr in args[6]]
    else:
        model.nurse_associations = []
    if number_of_args >= 8:
        model.nurse_incompatibilities = [TNursePair._make(npr) for npr in args[7]]
    else:
        model.nurse_incompatibilities = []


def setup_data(model):
    """ compute internal data """
    all_nurses = model.nurses
    model.vacations_by_nurse = {n: [vac_day for (vac_nurse_id, vac_day) in model.vacations if vac_nurse_id == n.name]
                                for n in model.nurses}
    # compute shift activities (start, end duration)
    model.shift_activities = {s: ShiftActivity(s.day, s.start_time, s.end_time) for s in model.shifts}
    model.nurses_by_id = {n.name: n for n in all_nurses}


def setup_variables(model):
    all_nurses, all_shifts = model.nurses, model.shifts
    model.nurse_assignment_vars = model.binary_var_matrix(all_nurses, all_shifts, 'NurseAssigned')
    model.nurse_work_time_vars = model.continuous_var_dict(all_nurses, lb=0, name='NurseWorkTime')
    model.nurse_over_average_time_vars = model.continuous_var_dict(all_nurses, lb=0,
                                                                   name='NurseOverAverageWorkTime')
    model.nurse_under_average_time_vars = model.continuous_var_dict(all_nurses, lb=0,
                                                                    name='NurseUnderAverageWorkTime')
    model.average_nurse_work_time = model.continuous_var(lb=0, name='AverageNurseWorkTime')


def setup_constraints(model):
    all_nurses = model.nurses
    all_shifts = model.shifts
    nurse_assigned_vars = model.nurse_assignment_vars
    nurse_work_time_vars = model.nurse_work_time_vars
    shift_activities = model.shift_activities
    nurses_by_id = model.nurses_by_id
    max_work_time = model.work_rules.work_time_max

    # define average
    model.add_constraint(
        len(all_nurses) * model.average_nurse_work_time == model.sum(
            model.nurse_work_time_vars[n] for n in model.nurses),
        "average")

    # compute nurse work time , average and under, over
    for n in all_nurses:
        work_time_var = nurse_work_time_vars[n]
        model.add_constraint(
            work_time_var == model.sum(nurse_assigned_vars[n, s] * shift_activities[s].duration for s in model.shifts),
            "work_time_%s" % str(n))
        model.add_constraint(work_time_var == model.average_nurse_work_time + model.nurse_over_average_time_vars[n] -
                             model.nurse_under_average_time_vars[n], "averag_work_time_%s" % str(n))

        model.add_constraint(work_time_var <= max_work_time, "max_time_%s" % str(n))

    # vacations
    for n in all_nurses:
        for vac_day in model.vacations_by_nurse[n]:
            for shift in (s for s in all_shifts if s.day == vac_day):
                model.add_constraint(nurse_assigned_vars[n, shift] == 0,
                                     "medium_vacations_%s_%s_%s" % (str(n), vac_day, str(shift)))

    # a nurse cannot be assigned overlapping shifts
    model.number_of_overlaps = 0
    for s1 in all_shifts:
        for s2 in all_shifts:
            if s1 != s2 and shift_activities[s1].overlaps(shift_activities[s2]):
                model.number_of_overlaps += 1
                for n in all_nurses:
                    model.add_constraint(nurse_assigned_vars[n, s1] + nurse_assigned_vars[n, s2] <= 1,
                                         "medium_overlapping_%s_%s_%s" % (str(s1), str(s2), str(n)))

    for s in all_shifts:
        demand_min = s.min_requirement
        demand_max = s.max_requirement
        model.add_range(demand_min, model.sum([nurse_assigned_vars[n, s] for n in model.nurses]), demand_max,
                        "medium_shift_%s" % str(s))

    for (dept, skill, required) in model.skill_requirements:
        if required > 0:
            for dsh in (s for s in all_shifts if dept == s.department):
                model.add_constraint(model.sum(nurse_assigned_vars[skilled_nurse, dsh] for skilled_nurse in
                                               (n for n in all_nurses if
                                                n.name in model.nurse_skills.keys() and skill in model.nurse_skills[
                                                    n.name])) >= required,
                                     "high_required_%s_%s_%s_%s" % (str(dept), str(skill), str(required), str(dsh)))

    # nurse-nurse associations
    c = 0
    for (first_nurse_id, second_nurse_id) in model.nurse_associations:
        if first_nurse_id in nurses_by_id and second_nurse_id in nurses_by_id:
            first_nurse = nurses_by_id[first_nurse_id]
            second_nurse = nurses_by_id[second_nurse_id]
            for s in all_shifts:
                c += 1
                ct_name = 'medium_ct_nurse_assoc%s_%s_%d' % (first_nurse_id, second_nurse_id, c)
                model.add_constraint(nurse_assigned_vars[first_nurse, s] == nurse_assigned_vars[second_nurse, s],
                                     ct_name)

    # nurse-nurse incompatibilities
    c = 0
    for (first_nurse_id, second_nurse_id) in model.nurse_incompatibilities:
        if first_nurse_id in nurses_by_id and second_nurse_id in nurses_by_id:
            first_nurse = nurses_by_id[first_nurse_id]
            second_nurse = nurses_by_id[second_nurse_id]
            for s in all_shifts:
                c += 1
                ct_name = 'medium_ct_nurse_incompat_%s_%s_%d' % (first_nurse_id, second_nurse_id, c)
                model.add_constraint(nurse_assigned_vars[first_nurse, s] + nurse_assigned_vars[second_nurse, s] <= 1,
                                     ct_name)

    model.nurse_costs = [model.nurse_assignment_vars[n, s] * n.payRate * model.shift_activities[s].duration for n in
                         model.nurses
                         for s in model.shifts]
    model.total_number_of_assignments = model.sum(
        model.nurse_assignment_vars[n, s] for n in model.nurses for s in model.shifts)
    model.total_salary_cost = model.sum(model.nurse_costs)


def setup_objective(model):
    model.add_kpi(model.total_salary_cost, "Total salary cost")
    model.add_kpi(model.total_number_of_assignments, "Total number of assignments")
    model.add_kpi(model.average_nurse_work_time)

    total_fairness = model.sum(model.nurse_over_average_time_vars[n] for n in model.nurses) + model.sum(
        model.nurse_under_average_time_vars[n] for n in model.nurses)
    model.add_kpi(total_fairness, "Total fairness")
    model.minimize(model.total_salary_cost + model.total_number_of_assignments + total_fairness)


def print_information(model):
    print("#departments=%d" % len(model.departments))
    print("#skills=%d" % len(model.skills))
    print("#shifts=%d" % len(model.shifts))
    print("#nurses=%d" % len(model.nurses))
    print("#vacations=%d" % len(model.vacations))
    print("#nurse associations=%d" % len(model.nurse_associations))
    print("#incompatibilities=%d" % len(model.nurse_incompatibilities))
    model.print_information()
    model.report_kpis()


def print_solution(model):
    print("*************************** Solution ***************************")
    print("Allocation By Department:")
    for d in model.departments:
        print ("\t{}: {}".format(d, sum(
            model.nurse_assignment_vars[n, s].solution_value for n in model.nurses for s in model.shifts if
            s.department == d)))
    print("Cost By Department:")
    for d in model.departments:
        cost = sum(
            model.nurse_assignment_vars[n, s].solution_value * n.payRate * model.shift_activities[s].duration for n in
            model.nurses for s in model.shifts if s.department == d)
        print("\t{}: {}".format(d, cost))
    print("Nurses Assignments")
    for n in sorted(model.nurses):
        total_hours = sum(
            model.nurse_assignment_vars[n, s].solution_value * model.shift_activities[s].duration for s in model.shifts)
        print("\t{}: total hours:{}".format(n.name, total_hours))
        for s in model.shifts:
            if model.nurse_assignment_vars[n, s].solution_value == 1:
                print ("\t\t{}: {} {}-{}".format(s.day.name, s.department, s.start_time, s.end_time))


SKILLS = ["Anaesthesiology",
          "Cardiac Care",
          "Geriatrics",
          "Oncology",
          "Pediatrics"
          ]

DEPTS = ["Consultation",
         "Emergency"
         ]

NURSES = [("Anne", 11, 1, 25),
          ("Bethanie", 4, 5, 28),
          ("Betsy", 2, 2, 17),
          ("Cathy", 2, 2, 17),
          ("Cecilia", 9, 5, 38),
          ("Chris", 11, 4, 38),
          ("Cindy", 5, 2, 21),
          ("David", 1, 2, 15),
          ("Debbie", 7, 2, 24),
          ("Dee", 3, 3, 21),
          ("Gloria", 8, 2, 25),
          ("Isabelle", 3, 1, 16),
          ("Jane", 3, 4, 23),
          ("Janelle", 4, 3, 22),
          ("Janice", 2, 2, 17),
          ("Jemma", 2, 4, 22),
          ("Joan", 5, 3, 24),
          ("Joyce", 8, 3, 29),
          ("Jude", 4, 3, 22),
          ("Julie", 6, 2, 22),
          ("Juliet", 7, 4, 31),
          ("Kate", 5, 3, 24),
          ("Nancy", 8, 4, 32),
          ("Nathalie", 9, 5, 38),
          ("Nicole", 0, 2, 14),
          ("Patricia", 1, 1, 13),
          ("Patrick", 6, 1, 19),
          ("Roberta", 3, 5, 26),
          ("Suzanne", 5, 1, 18),
          ("Vickie", 7, 1, 20),
          ("Wendie", 5, 2, 21),
          ("Zoe", 8, 3, 29)
          ]

SHIFTS = [("Emergency", Weekday.Monday, 2, 8, 3, 5),
          ("Emergency", Weekday.Monday, 8, 12, 4, 7),
          ("Emergency", Weekday.Monday, 12, 18, 2, 5),
          ("Emergency", Weekday.Monday, 18, 2, 3, 7),
          ("Consultation", Weekday.Monday, 8, 12, 10, 13),
          ("Consultation", Weekday.Monday, 12, 18, 8, 12),
          ("Cardiac Care", Weekday.Monday, 8, 12, 10, 13),
          ("Cardiac Care", Weekday.Monday, 12, 18, 8, 12),
          ("Emergency", Weekday.Tuesday, 8, 12, 4, 7),
          ("Emergency", Weekday.Tuesday, 12, 18, 2, 5),
          ("Emergency", Weekday.Tuesday, 18, 2, 3, 7),
          ("Consultation", Weekday.Tuesday, 8, 12, 10, 13),
          ("Consultation", Weekday.Tuesday, 12, 18, 8, 12),
          ("Cardiac Care", Weekday.Tuesday, 8, 12, 4, 7),
          ("Cardiac Care", Weekday.Tuesday, 12, 18, 2, 5),
          ("Cardiac Care", Weekday.Tuesday, 18, 2, 3, 7),
          ("Emergency", Weekday.Wednesday, 2, 8, 3, 5),
          ("Emergency", Weekday.Wednesday, 8, 12, 4, 7),
          ("Emergency", Weekday.Wednesday, 12, 18, 2, 5),
          ("Emergency", Weekday.Wednesday, 18, 2, 3, 7),
          ("Consultation", Weekday.Wednesday, 8, 12, 10, 13),
          ("Consultation", Weekday.Wednesday, 12, 18, 8, 12),
          ("Emergency", Weekday.Thursday, 2, 8, 3, 5),
          ("Emergency", Weekday.Thursday, 8, 12, 4, 7),
          ("Emergency", Weekday.Thursday, 12, 18, 2, 5),
          ("Emergency", Weekday.Thursday, 18, 2, 3, 7),
          ("Consultation", Weekday.Thursday, 8, 12, 10, 13),
          ("Consultation", Weekday.Thursday, 12, 18, 8, 12),
          ("Emergency", Weekday.Friday, 2, 8, 3, 5),
          ("Emergency", Weekday.Friday, 8, 12, 4, 7),
          ("Emergency", Weekday.Friday, 12, 18, 2, 5),
          ("Emergency", Weekday.Friday, 18, 2, 3, 7),
          ("Consultation", Weekday.Friday, 8, 12, 10, 13),
          ("Consultation", Weekday.Friday, 12, 18, 8, 12),
          ("Emergency", Weekday.Saturday, 2, 12, 5, 7),
          ("Emergency", Weekday.Saturday, 12, 20, 7, 9),
          ("Emergency", Weekday.Saturday, 20, 2, 12, 12),
          ("Emergency", Weekday.Sunday, 2, 12, 5, 7),
          ("Emergency", Weekday.Sunday, 12, 20, 7, 9),
          ("Emergency", Weekday.Sunday, 20, 2, 12, 12),
          ("Geriatrics", Weekday.Sunday, 8, 10, 2, 5)]

NURSE_SKILLS = {"Anne": ["Anaesthesiology", "Oncology", "Pediatrics"],
                "Betsy": ["Cardiac Care"],
                "Cathy": ["Anaesthesiology"],
                "Cecilia": ["Anaesthesiology", "Oncology", "Pediatrics"],
                "Chris": ["Cardiac Care", "Oncology", "Geriatrics"],
                "Gloria": ["Pediatrics"], "Jemma": ["Cardiac Care"],
                "Joyce": ["Anaesthesiology", "Pediatrics"],
                "Julie": ["Geriatrics"], "Juliet": ["Pediatrics"],
                "Kate": ["Pediatrics"], "Nancy": ["Cardiac Care"],
                "Nathalie": ["Anaesthesiology", "Geriatrics"],
                "Patrick": ["Oncology"], "Suzanne": ["Pediatrics"],
                "Wendie": ["Geriatrics"],
                "Zoe": ["Cardiac Care"]
                }

VACATIONS = [("Anne", Weekday.Friday),
             ("Anne", Weekday.Sunday),
             ("Cathy", Weekday.Thursday),
             ("Cathy", Weekday.Tuesday),
             ("Joan", Weekday.Thursday),
             ("Joan", Weekday.Saturday),
             ("Juliet", Weekday.Monday),
             ("Juliet", Weekday.Tuesday),
             ("Juliet", Weekday.Thursday),
             ("Nathalie", Weekday.Sunday),
             ("Nathalie", Weekday.Thursday),
             ("Isabelle", Weekday.Monday),
             ("Isabelle", Weekday.Thursday),
             ("Patricia", Weekday.Saturday),
             ("Patricia", Weekday.Wednesday),
             ("Nicole", Weekday.Friday),
             ("Nicole", Weekday.Wednesday),
             ("Jude", Weekday.Tuesday),
             ("Jude", Weekday.Friday),
             ("Debbie", Weekday.Saturday),
             ("Debbie", Weekday.Wednesday),
             ("Joyce", Weekday.Sunday),
             ("Joyce", Weekday.Thursday),
             ("Chris", Weekday.Thursday),
             ("Chris", Weekday.Tuesday),
             ("Cecilia", Weekday.Friday),
             ("Cecilia", Weekday.Wednesday),
             ("Patrick", Weekday.Saturday),
             ("Patrick", Weekday.Sunday),
             ("Cindy", Weekday.Sunday),
             ("Dee", Weekday.Tuesday),
             ("Dee", Weekday.Friday),
             ("Jemma", Weekday.Friday),
             ("Jemma", Weekday.Wednesday),
             ("Bethanie", Weekday.Wednesday),
             ("Bethanie", Weekday.Tuesday),
             ("Betsy", Weekday.Monday),
             ("Betsy", Weekday.Thursday),
             ("David", Weekday.Monday),
             ("Gloria", Weekday.Monday),
             ("Jane", Weekday.Saturday),
             ("Jane", Weekday.Sunday),
             ("Janelle", Weekday.Wednesday),
             ("Janelle", Weekday.Friday),
             ("Julie", Weekday.Sunday),
             ("Kate", Weekday.Tuesday),
             ("Kate", Weekday.Monday),
             ("Nancy", Weekday.Sunday),
             ("Roberta", Weekday.Friday),
             ("Roberta", Weekday.Saturday),
             ("Janice", Weekday.Tuesday),
             ("Janice", Weekday.Friday),
             ("Suzanne", Weekday.Monday),
             ("Vickie", Weekday.Wednesday),
             ("Vickie", Weekday.Friday),
             ("Wendie", Weekday.Thursday),
             ("Wendie", Weekday.Saturday),
             ("Zoe", Weekday.Saturday),
             ("Zoe", Weekday.Sunday)]

NURSE_ASSOCIATIONS = [("Isabelle", "Dee"),
                      ("Anne", "Patrick")]

NURSE_INCOMPATIBILITIES = [("Patricia", "Patrick"),
                           ("Janice", "Wendie"),
                           ("Suzanne", "Betsy"),
                           ("Janelle", "Jane"),
                           ("Gloria", "David"),
                           ("Dee", "Jemma"),
                           ("Bethanie", "Dee"),
                           ("Roberta", "Zoe"),
                           ("Nicole", "Patricia"),
                           ("Vickie", "Dee"),
                           ("Joan", "Anne")
                           ]

SKILL_REQUIREMENTS = [("Emergency", "Cardiac Care", 1)]

DEFAULT_WORK_RULES = TWorkRules(40)


def build(docloud_context=None):
    model = Model("Nurses", docloud_context=docloud_context)
    load_data(model, DEPTS, SKILLS, SHIFTS, NURSES, NURSE_SKILLS, VACATIONS, NURSE_ASSOCIATIONS,
              NURSE_INCOMPATIBILITIES)
    setup_data(model)
    setup_variables(model)
    setup_constraints(model)
    setup_objective(model)
    return model


def run(docloud_context=None):
    model = build(docloud_context=docloud_context)
    status = solve(model)
    return status


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

    from docplex.mp.environment import Environment

    env = Environment()
    env.print_information()

    run(ctx)
