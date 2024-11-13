import subprocess
from argparse import ArgumentParser
from itertools import product

def get_input(input_file_name):
    """
    function for retrieving the Nonogram from a file
    needed input:
        - n := grid side (n*n := grid size)
        - row_rules := list of lists, represents row constraints
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

def generate_patterns(length, groups):
    min_length = sum(groups) + len(groups) - 1
    if min_length > length:
        return []
    
    patterns = []
    n_spaces = length - sum(groups)
    for spaces in product(range(n_spaces + 1), repeat=len(groups) + 1):
        if sum(spaces) == n_spaces:
            pattern = [0] * length
            pos = spaces[0]

            for group, space in zip(groups, spaces[1:]):
                if pos + group > length:
                    break 
                for _ in range(group):
                    pattern[pos] = 1
                    pos += 1
                pos += space + 1 
            else:
                patterns.append(pattern)
    return patterns

def encode(n, row_rules, col_rules, output_name):
    with open(output_name, "w") as cnf_file:
        clauses = []
        var_map = lambda i,j: i * n + j + 1

        for i, row_rule in enumerate(row_rules):
            row_patterns = generate_patterns(n, row_rule)
            pattern_clauses = []
            if not row_patterns:
                print(f"ERROR: No valid patterns found for row {i} with rule {row_rule}")
                continue
        
            for pattern in row_patterns:
                clause = []

                for j, value in enumerate(pattern):
                    var = var_map(i, j)
                    if value == 1:
                        clause.append(str(var))  
                    else:
                        clause.append(f"{-var}")  

                clauses.append(" ".join(clause) + " 0")  
                pattern_clauses.append(clause)

            for p1 in range(len(pattern_clauses)):
                for p2 in range(p1 + 1, len(pattern_clauses)):
                    exclusivity_clause = []
                    exclusivity_clause.extend(-lit for lit in pattern_clauses[p1])
                    exclusivity_clause.extend(-lit for lit in pattern_clauses[p2])
                    clauses.append(" ".join(map(str, exclusivity_clause)) + " 0")
            print(f"DEBUG: Row {i} patterns: {row_patterns}")

        for j, col_rule in enumerate(col_rules):
            col_patterns = generate_patterns(n, col_rule)
            pattern_clauses = []

            if not col_patterns:
                print(f"ERROR: No valid patterns found for column {j} with rule {col_rule}")
                continue

            for pattern in col_patterns:
                clause = []

                for i, value in enumerate(pattern):
                    var = var_map(i, j)
                    if value == 1:
                        clause.append(str(var)) 
                    else:
                        clause.append(f"-{var}") 

                clauses.append(" ".join(clause) + " 0")  
                pattern_clauses.append(clause)
          
            for p1 in range(len(pattern_clauses)):
                for p2 in range(p1 + 1, len(pattern_clauses)):
                    exclusivity_clause = []
                    exclusivity_clause.extend(-lit for lit in pattern_clauses[p1])
                    exclusivity_clause.extend(-lit for lit in pattern_clauses[p2])
                    clauses.append(" ".join(map(str, exclusivity_clause)) + " 0")
            print(f"DEBUG: Column {j} patterns: {col_patterns}")

        cnf_file.write(f"p cnf {n * n} {len(clauses)}\n")
        for clause in clauses:
            cnf_file.write(clause + "\n")
            print(f"DEBUG: Clause added: {clause}")  #

def call_solver(cnf_file, solver_name="glucose"):
    output_file = "output.model"
    with open(output_file, "w") as out_file:
        result = subprocess.run([solver_name, cnf_file], stdout=out_file, stderr=subprocess.PIPE, text=True)

        if result.returncode == 10:  # SATISFIABLE
            with open(output_file, "r") as file:
                output = file.read()
            return output
        elif result.returncode == 20:  # UNSATISFIABLE
            print("No solution found")
            return None
        else:
            print("Error:", result.stderr)
            return None

def parse_solution(result, n):
    if result is None:
        print("No solution found")
        return None

    grid = [[0] * n for _ in range(n)]
    for line in result.splitlines():
        if line.startswith("v"):
            vars = map(int, line.split()[1:])
            for var in vars:
                if var > 0:
                    i = (var - 1) // n
                    j = (var - 1) % n
                    grid[i][j] = 1
                else:
                    i = (-var - 1) // n
                    j = (-var - 1) % n
                    grid[i][j] = 0
                print(f"DEBUG: Variable {var} set grid[{i}][{j}] to {'#' if grid[i][j] == 1 else '.'}")

    print("Solution found:")
    for row in grid:
        for cell in row:
            if cell == 1:
                print("#", end=" ")
            else:
                print(".", end=" ")
        print()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="Input file with Nonogram instance")
    parser.add_argument("-o", "--output", default="nonogram.cnf", type=str, help="Output file for CNF formula")
    parser.add_argument("-s", "--solver", default="glucose", type=str, help="The SAT solver to use")
    parser.add_argument("-v", "--verbosity", default=1, type=int, choices=range(2), help="Solver verbosity")
    args = parser.parse_args()

    n, row_rules, col_rules = get_input(args.input)
    
    encode(n, row_rules, col_rules, args.output)

    result = call_solver(args.output, args.solver)
    parse_solution(result, n)