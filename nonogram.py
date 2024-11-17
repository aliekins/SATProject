import subprocess
from argparse import ArgumentParser
from itertools import combinations

def get_input(input_file_name):
    """
    function for retrieving the Nonogram from a file
    needed input:
        - n := grid side (n*n := grid size)
        - row_rules := list of lists, represents row constraints (sizes of blocks of each row)
        - column_rules := -||- but for columns
    """
    with open(input_file_name, "r") as file:
        n = int(file.readline().strip())        

        # reading row rules
        row_rules = []
        for _ in range(n):
            row_rules.append(list(map(int, file.readline().strip().split())))
        
        # reading column rules
        column_rules = []
        for _ in range(n):
            column_rules.append(list(map(int, file.readline().split())))

    return n, row_rules, column_rules

def block_filled_at_least_once(num_block, n, cnf):
    temp = []
    start = (num_block - 1) * n + 1
    end = num_block * n
    for i in range (start, end + 1):
        temp.append(i) 
    cnf.append(temp)
    return cnf

def block_starts_at_most_once(num_block, n, cnf):
    start = (num_block - 1) * n + 1
    end = num_block * n

    for i in range(start, end + 1):
        for j in range(i, end + 1):
            if i != j:
                cnf.append([-i, -j])

# def no_two_blocks_overlap(block_num, rules, rules_vars, cnf):
#     current_block_vars = rules_vars[block_num - 1]
#     # print(f"{current_block_vars}")

#     if block_num < len(rules_vars):
#         next_block_vars = rules_vars[block_num]
#         # print(f"{next_block_vars}")
#     else: 
#         return
    
#     current_block_length = 
#     for start_indx in range(len(current_block_vars)):
#         current_start = current_block_vars[start_indx]

#         forbidden_start = start_indx + current_block_length + 1

#         for next_start_indx in range(forbidden_start, len(next_block_vars)):
#             next_start = next_block_vars[next_start_indx]

#             cnf.append([-current_start, -next_start])

def calculate_block_positions(rules, n, start_indx):
    positions = []
    current_start = start_indx

    for rule in rules:
        for block in range(len(rule)):
            min_pos = current_start
            max_pos = current_start + n

            block_pos = list(range(min_pos, max_pos))
            positions.append(block_pos)

            current_start = max_pos
    return positions

def encode(n, row_rules, col_rules):
    cnf = []
    num_vars = 0
    position_var_rows = calculate_block_positions(row_rules, n, start_indx=1)
    position_var_cols = calculate_block_positions(col_rules, n, start_indx=1 + + sum(len(row) for row in row_rules) * n)

    print(f"{row_rules}")
    print(f"{col_rules}")
    print(f"{position_var_rows}")
    print(f"{position_var_cols}")

    for block in range(1, len(position_var_rows) + 1):
        block_filled_at_least_once(block, n, cnf)
        block_starts_at_most_once(block, n, cnf)

    block_num = 1
    for r in row_rules:
        for block in position_var_rows:
            # no_two_blocks_overlap(block_num, row_rules, position_var_rows, cnf)
            block_num += 1

    return cnf, num_vars

def call_solver(cnf, num_vars, output_name, solver_name, verbosity):
    """
    writes the CNF formula to a file and calls external SAT solver
        - cnf: list of CNF clauses 
        - num_vars: count of all variables
        - output_name: file where CNF will be saved
    returns:
        - solver result found by subporocess
    """
    # writing clauses to the output CNF file
    with open(output_name, "w") as cnf_file:
        cnf_file.write(f"p cnf {num_vars} {len(cnf)}\n")

        for clause in cnf:
            cnf_file.write(" ".join(map(str, clause)) + " 0\n")

    result = subprocess.run(
        [solver_name, output_name, '-model', '-verb=' + str(verbosity)],
        stdout=subprocess.PIPE,
        text=True
    )
    print("Debug: Raw solver output:\n", result.stdout) 
    return result

def parse_solution(result, n):
    """
    interprets the SAT solver output
    - result : raw slution for the solver
    """
    if "UNSAT" in result.stdout:
        print("No solution found")
        return None

    print("Solution found\n")

    model = []
    for line in result.stdout.splitlines():
        if line.startswith("v"):
            model.extend(int(x) for x in line.split()[1:] if x != "0")

    print("Debug: Extracted model from solver output:", model)
    
    grid = [[" " for _ in range(n)] for _ in range(n)]

    for var in model:
        if abs(var) <= n * n:  
            i = (abs(var) - 1) // n
            j = (abs(var) - 1) % n
        if var > 0:
            print(f"Debug: Filling cell at ({i}, {j}) based on variable {var}")
            grid[i][j] = "#"
        else:
            grid[i][j] = "."
    
    for row in grid:
        print(" ".join(row))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="Input file with Nonogram instance")
    parser.add_argument("-o", "--output", default="nonogram.cnf", type=str, help="Output file for CNF formula")
    parser.add_argument("-s", "--solver", default="glucose", type=str, help="The SAT solver to use")
    parser.add_argument("-v", "--verbosity", default=1, type=int, choices=range(2), help="Solver verbosity")
    args = parser.parse_args()

    n, row_rules, col_rules = get_input(args.input)
    
    cnf, num_vars = encode(n, row_rules, col_rules)

    result = call_solver(cnf, num_vars, args.output, args.solver, args.verbosity)
    parse_solution(result, n)