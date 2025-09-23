from pulp import *

def solve_station_conflict(train_data, headway_time=5):

    problem = LpProblem("Station_Precedence_Problem", LpMinimize)

    trains = train_data.keys()

    t = LpVariable.dicts("arrival_time", trains, lowBound=0, cat='Continuous')
    y = LpVariable.dicts("precedence_decision", [(i, j) for i in trains for j in trains if i != j], cat='Binary')

    problem += lpSum(train_data[i]['priority'] * (t[i] - train_data[i]['eta']) for i in trains), "Total_Weighted_Delay"

    for i in trains:
        problem += t[i] >= train_data[i]['eta'], f"Arrival_Time_Constraint_{i}"

    for i in trains:
        for j in trains:
            if i != j:
                problem += t[i] + headway_time <= t[j] + 1000 * (1 - y[(i, j)]), f"Precedence_Constraint_1_{i}_{j}"
                problem += t[j] + headway_time <= t[i] + 1000 * y[(i, j)], f"Precedence_Constraint_2_{i}_{j}"

    problem.solve(PULP_CBC_CMD(msg=0))

    if LpStatus[problem.status] == 'Optimal':
        results = {}
        for i in trains:
            results[i] = {
                'new_arrival_time': value(t[i]),
                'delay_minutes': value(t[i]) - train_data[i]['eta']
            }
        
        precedence = {}
        for (i, j) in y:
            if value(y[(i, j)]) == 1:
                precedence[(i, j)] = 'Train ' + str(i) + ' arrives before Train ' + str(j)

        return results, precedence

    else:
        return {"status": "No optimal solution found"}, None

if __name__ == '__main__':
    train_data = {
        'Train1': {'eta': 90, 'priority': 10},
        'Train2': {'eta': 92, 'priority': 5},
        'Train3': {'eta': 90, 'priority': 10},
        'Train4': {'eta': 90, 'priority': 10}

    }
    
    optimized_schedule, precedence_decisions = solve_station_conflict(train_data)
    
    print("Optimized Schedule:")
    print(optimized_schedule)
    print("\nPrecedence Decisions:")
    print(precedence_decisions)