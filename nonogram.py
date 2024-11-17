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

def block_filled_at_least_once(block_indx, block_length, n, cnf):
    temp = []
    start = block_indx * n + 1
    end = (block_indx + 1)* n - (block_length - 1)
    for i in range (start, end + 1):
        temp.append(i) 
    cnf.append(temp)
    return cnf

def block_starts_at_most_once(block_indx, n, cnf):
    start = block_indx * n + 1
    end = (block_indx + 1) * n

    for i in range(start, end + 1):
        for j in range(i, end + 1):
            if i != j:
                cnf.append([-i, -j])
    return cnf

def no_two_blocks_overlap(block_num, block_length, num_next_blocks, cnf, n):
    block_var_offset = block_num * n
    for pos in range(1, n + 1):
        for k in range(1, num_next_blocks + 1):
            for pair in range(1, pos + block_length + 1):
                if (block_var_offset + (k + 1) * n + 1 > block_var_offset + k * n + pair):
                    cnf.append([-(pos + block_var_offset), -(block_var_offset + k*n + pair)])
                else:
                    cnf.append([-(pos + block_var_offset)])
    return cnf

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

def calculate_block_positions_col(col, col_num, row_rules, cnf):
    min_filled_in_column(sum(col), col_num, row_rules, cnf)
    return cnf

def min_filled_in_column(num_filled, col_num, row_rules, cnf):
    block_number = 0
    vars = []
    vars_neg = []
    for r_indx, rule in enumerate(row_rules):
        temp = []
        temp_neg = []
        for b_indx, block in enumerate(rule):
            block_offset = block_number * n
            for i in range(block):
                if(block_offset < (block_offset + col_num - i)):
                    temp.append(block_offset + col_num - i)
                    temp_neg.append(-(block_offset + col_num - i))
            block_number += 1
        vars.append(temp)
        vars_neg.append(temp_neg)
    cnf = choose_filled_in_column(vars, vars_neg, num_filled, cnf)

def choose(lists, cnf):
    print(f"sent in : {lists}")
    num_of_comb = 1
    for lst in lists:
        num_of_comb *= len(lst)

    indexes = [0] * len(lists)  

    for c in range(num_of_comb):
        temp = [lists[i][indexes[i]] for i in range(len(lists))]
        cnf.append(temp)

        for i in range(len(indexes) - 1, -1, -1): 
            indexes[i] += 1
            if indexes[i] < len(lists[i]):  
                break
            indexes[i] = 0  

    return cnf

def choose_filled_in_column(vars, neg_vars, num_filled, cnf):
    if num_filled == 0:
        for i in neg_vars:
            for j in i:
                for k in j:
                    cnf.append([k])

    elif num_filled == 1:
        temp1 = []
        for i in vars:
            for j in i:
                temp1.append(j)
        cnf.append(temp1)
        for i in combinations(neg_vars, 2):
            # print(f"i:{i}")
            temp2 = []
            for j in i:
                for k in j:
                    # print(f"k:{k}", end=", ")
                    temp2.append(k)
            cnf.append(temp2)
    # elif len(vars[i] for i in vars) == 1:
    else:
        # for i in combinations(vars, num_filled):
        #     print(f"RUNNING CHOOSE on {i}")
        #     cnf = choose(i, cnf)
        for i in combinations(vars, num_filled):
            temp = []
            for j in i:
                for k in j:
                    temp.append(k)
            cnf.append(temp)

        for i in combinations(neg_vars, num_filled + 1):
            print(f"RUNNING CHOOSE on {i}")
            cnf = choose(i, cnf)
    
    return cnf

def encode(n, row_rules, col_rules):
    cnf = []
    position_var_rows = calculate_block_positions(row_rules, n, start_indx=1)
    
    block_indx = 0
    for row in row_rules:
        for block in row:
            cnf = block_filled_at_least_once(block_indx, block, n, cnf)
            cnf = block_starts_at_most_once(block_indx, n, cnf)
            block_indx += 1

    block_num = 0
    for r in row_rules:
        processed_blocks = 1
        for i in r:
            print("RAN 2")
            cnf = no_two_blocks_overlap(block_num, r[processed_blocks-1], len(r) - processed_blocks, cnf, n)
            processed_blocks += 1
            block_num += 1

    for c_indx, col in enumerate(col_rules):
        print("RAN 3")
        cnf = calculate_block_positions_col(col, c_indx + 1, row_rules, cnf)

    num_vars = block_num * n
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
    
    grid = [["." for _ in range(n)] for _ in range(n)]

    block_starts = []
    for var in model:
        if var > 0:
            num = var % n
            if num == 0:
                num = n
            block_starts.append(num - 1)
    # print(block_starts)

    block_index = 0
    for row, row_rule in enumerate(row_rules):
        for r_indx, rule in enumerate(row_rule):
            for i in range(rule):
                grid[row][block_starts[block_index] + i] = "#"  
            block_index += 1          
    
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