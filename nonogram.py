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

    def place_blocks(block_idx, pos, placement):
        # recursively generating placements for each block
        if block_idx == len(blocks):       # base case - all blocks placed
            for empty_pos in range(pos, length):      # filling the remaining cells with 'empty' clause
                placement.append(-cell_fn(empty_pos))
            valid_placements.append(placement[:])
            return

        block_size = blocks[block_idx]

        while pos + block_size <= length:
            new_placement = placement[:]     # copying current placement 
            
            # adding current block's cells - 'filled' clause
            for k in range(block_size):
                new_placement.append(cell_fn(pos + k))
            
            if pos + block_size < length:      # if I am not at the end of the line - there must be space after the block
                new_placement.append(-cell_fn(pos + block_size))
            
            place_blocks(block_idx + 1, pos + block_size + 1, new_placement)   # calling to place the next block
            pos += 1

    place_blocks(0, 0, [])

    for placement in valid_placements:
        clauses.append(placement)

    return clauses

def encode(n, row_rules, col_rules, output_name):
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

    # writing clauses to the output CNF file
    with open(output_name, "w") as cnf_file:
        cnf_file.write(f"p cnf {var_count} {len(clauses)}\n")

        for clause in clauses:
            cnf_file.write(" ".join(map(str, clause)) + " 0\n")

def call_solver(cnf_file, solver_name="glucose"):
    """
    calls an external SAT solver to attempt solving the CNF formula
    - cnf_file: contains encoded Nonogram
    """
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
    """
    interprets the SAT solver output
    - result : raw slution for the solver
    """
    if result is None:
        print("No solution found")
        return None

    print("Solution found")

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