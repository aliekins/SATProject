import subprocess
from argparse import ArgumentParser
from itertools import product

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

def generate_block_placements(blocks, length, cell_fn):
    """
    generates clauses for placing a sequence of blocks within a line of given length
        - blocks: list of block sizes
        - length: total length/number of cells in the line (row or column)
        - cell_fn: returns the CNF variable for a given position in the line
    returns:
        - list of CNF clauses representing valid block placement
    """
    clauses = []
    valid_placements = []
    
    # iterating through each possible start position for blocks
    for start_pos in range(length - sum(blocks) - len(blocks) + 1 + 1):
        placement = []

        # filling leading empty cells before the block sequence starts
        for empty_pos in range(start_pos):
            placement.append(-cell_fn(empty_pos))

        # placing blocks with necessary gaps between them
        pos = start_pos
        for block_idx, block_size in enumerate(blocks):
            # adding filled cells for the current block
            for k in range(block_size):
                placement.append(cell_fn(pos + k))
            pos += block_size

            # adding an empty cell as a gap between blocks, if more blocks are to follow
            if block_idx < len(blocks) - 1:
                placement.append(-cell_fn(pos))
                pos += 1

        # filling trailing empty cells after the block sequence ends
        for empty_pos in range(pos, length):
            placement.append(-cell_fn(empty_pos))

        # adding this placement as a valid configuration
        valid_placements.append(placement)

    # adding all valid placements to clauses
    for placement in valid_placements:
        clauses.append(placement)

    return clauses

def encode(n, row_rules, col_rules):
    """
    encodes the Nonogram puzzle into CNF format
        - n: size of the grid (n x n)
        - row_rules, col_rules: constraints for rows, columns
        - output_name: file to store the CNF formula
    """
    clauses = []
    var_count = n * n  # each cell is being represented as a variable

    def cell_var(i, j):
        # creating unique variable index for cell (i,j)
        return i * n + j + 1

    # row constraints - generating clauses for each row
    for i, blocks in enumerate(row_rules):
        if not blocks:  # no blocks, row should be all empty
            clauses.append([-cell_var(i, j) for j in range(n)])
        else:
            row_clauses = generate_block_placements(blocks, n, lambda j: cell_var(i, j))
            clauses.extend(row_clauses)
        print(f"DEBUG: Row {i + 1} clauses count: {len(row_clauses)}")

    # analogous for column constraints
    for j, blocks in enumerate(col_rules):
        if not blocks:  
            clauses.append([-cell_var(i, j) for i in range(n)])
        else:
            col_clauses = generate_block_placements(blocks, n, lambda i: cell_var(i, j))
            clauses.extend(col_clauses)
        print(f"DEBUG: Column {j + 1} clauses count: {len(col_clauses)}")

    return clauses, var_count

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
    print("Debug: Raw solver output:\n", result.stdout)  # Debugging: print raw solver output
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
        if var > 0:
            cell_num = var - 1
            i = cell_num // n
            j = cell_num % n
            print(f"Debug: Filling cell at ({i}, {j}) based on variable {var}")
            grid[i][j] = "#"
    
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