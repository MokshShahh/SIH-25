from pulp import *

def optimize_train_schedule_milp(train_routes):
    problem = LpProblem("Station_Precedence_Problem", LpMinimize)
    trains = train_routes.keys()

    t = LpVariable.dicts("arrival_time", trains, lowBound=0, cat='Continuous')
    y = LpVariable.dicts(
        "precedence_decision",
        [(i, j) for i in trains for j in trains if i != j],
        cat='Binary'
    )

    problem += lpSum(train_routes[i]['priority'] * (t[i] - train_routes[i]['eta']) for i in trains), "Total_Weighted_Delay"

    for i in trains:
        problem += t[i] >= train_routes[i]['eta'], f"Arrival_Time_Constraint_{i}"

    headway_time = 5
    M = 1000 
    for i in trains:
        for j in trains:
            if i != j:
                problem += t[i] + headway_time <= t[j] + M * (1 - y[(i, j)]), f"Precedence_Constraint_1_{i}_{j}"
                problem += t[j] + headway_time <= t[i] + M * y[(i, j)], f"Precedence_Constraint_2_{i}_{j}"

    problem.solve(PULP_CBC_CMD(msg=0))

    if LpStatus[problem.status] == 'Optimal':
        optimized_times = {i: {'new_arrival_time': value(t[i]), 'delay_minutes': value(t[i] - train_routes[i]['eta'])} for i in trains}
        precedence = {(i,j): 'Train {} before Train {}'.format(i,j) for (i,j) in y if value(y[(i,j)]) == 1}
        return optimized_times, precedence
    else:
        return None, None