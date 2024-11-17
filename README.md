# SATProject - Nonogram
## Contents
1. [Problem Description](#problem-description)
2. [Encoding](#encoding)
   - [Definitions/Setup](#definitionssetup)
   - [Row Constraints](#row-constraints)
   - [Column Constraints](#column-constraints)
   - [CNF Formulation](#cnf-formulation)
   - [Example](#example)
4. [User Documentation](#user-documentation)
5. [Examples](#examples)
6. [Experiments](#experiments)
7. [Sources and References](#sources-and-references)
   
## Problem Description
A Nonogram, in some countries also known as a Japanese puzzle, is a logic
puzzle, where the goal is to draw a rectangular image that follows certain row
and column constraints[^1].

Rules are : 
 - there is a grid of squares, which is supossed to be filled in black or marked as empty
 - rows and columns have listed lengths/rules which dictate the consecutive black squares of that row or column
 - the goal is to fill in the black squares so that both row and column rules are satisfied

Some examples of the online GUI enhanced puzzle can be found [here](https://www.puzzle-nonograms.com/). <br>

For this task the input format is, however, a bit different.
An example of a valid input format:
```
5
1 1 1
5
3
1 1
3
2
4
3 1
4
2
```
1. line - grid size (n) := number of squares per row/column
2. consecutive lines of rules, starting with row constraints
So, in this case from (1, 1, 1) to (2) [excluding (2)] are row rules and from (2) till the end of the input are column rules.

And the targeted nonogram in this case would be:
```
# . # . #
# # # # #
. # # # .
. # . # .
. # # # .
```
<sup>  Example found [here](https://nonogramskatana.wordpress.com/tag/5x5/) </sup>

> [!IMPORTANT]
> For (this)[./nonogram.py] version (nonogram.py), if there is a rule for 0 blocks in a row/column, the line should be left EMPTY. For the other version, 0 should be placed

## Encoding[^2]
#### Definitions/Setup
Assuming:
 - $n$  := grid dimension
 - $C_{i,j}$  := cell in i-th row and j-th column
Defining:
 - $x_{i,j}$ := propositional variable indicating whether $C_{i,j}$  is filled
   
#### Row Constraints
For each row $i$ with constraints $[k_1, k_2,\dots,k_m]$ :
1. defining possible placements for each block $k_p$ starting from different positions in the row
2. ensuring block do not overlap

For each possible starting position $s_p$ of block $k_p$:
 - $x_{i,s_p} \land x_{i,s_{p+1}} \land \dots \land x_{i,s_p+k_p-1}$ <br>
<sub>indicating that $k_p$ consecutie cells (starting at $s_p$) are filled</sub>
 - ensuring spacing between blocks
     - if $k_p$ ends at $s_p+k_p-1$ then the next block must start after at least one empty cell
     - adding constraint that cell $C_{i,s_p+k_p-1}$ is empty

#### Column Constraints
Analogous to row constraints - For each column $j$ with constraints /dots

#### CNF Formulation
Converting constraints to CNF:
1. **AND** - all cells within a block/group must be filled (converting each **AND** sequence into clauses)
2. **OR** - all valid block placements within a row/column must be generated (**OR** clauses covering all possible starting points - at least one placement needs to be chosen)
3. **SPACING + OVERLAPP** - constraints for cells between blocks to be empty

#### Example
We have a row of length 5 (5 cells) and constraint (2, 1)
Possibilites are:
- first block of two cells starts at position 0, second block of one cell can be placed at positions 3 or 4:
  - *Option 1:* $x_{i,0} \land x_{i,1} \land \neg x_{i,2} \land x_{i3}$ (in such case $\neg x_{i,4}$
  - *Option 2:*  $x_{i,0} \land x_{i,1} \land \neg x_{i,2} \land \neg x_{i3} \land x_{i,4}$
 
Of course, this is just DNF. For CNF, different methods need to be used. There is brute force, used in [one version](./inefficient_nonogram.py) and there is a more thought through approach, seen in [the other version](./nonogram.py). In the brute force approach, I create all possible groups of a row/column as described above. Then, there are two possible functions to call, which return the groups' CNF form. 

Function `to_cnf` creates all possible combinations for the elements of the group, which in `dnf_to_cnf` function is achieved by "logical multiplication". The only real difference between them, is that I coded `to_cnf` and `dnf_to_cnf` uses itertools' function `product`. Both of them work great for smaller nonograms, the sizes up to 5x5, no matter the complexity, are resolved rather fast. However, after the 6x6 mark, if the complexity of the puzzle is greater (small amounts of groups and many placement posibilities), the brute force approach takes long and at times does not even compile since it gets killed. The issue with big recursion depth is resolved by calling the `to_cnf` function instead of `dnf_to_cnf`, but still, the process gets killed due to Memory Exceptions, since number of clauses is exponential.

[Nonogram.py](./nonogram.py), on the other hand, is a bit more complex. The idea was to encode the individual blocks, instead of cells, and thus, if you run it, the `[OUTPUT].cnf` file might seem unreadable, but here is the key.
 - block := rule defined in input (consecutive filled cells of a row/column)
 - variables := created for each block/rule made in the rows, with offset $n * previousBlocks_{count}$ (n := length of the row)
 - cnf tells us := starting position of each block, based on their offsets

#### Row Constraints
for each block applies:
 - it has to be placed in the row at least once - function `block_filled_at_least_once`
      - $var_1 \lor var_2 \lor \dots \lor var_n$
      - where $var_i$ is the variable of the block from start position being $n * block_indx + 1$ and end position being the $offset + n$
 - the block cannot start, if its length would exceed the grid - function `block_filled_at_least_once`
      - incorporated by adjusting the previous condition for ending position to be
      - $offset + n - length_b - 1$ for $length_b =$ length of block 
 - it has to be placed in the row at most once (cannot have starting index at more than one cell) - function `block_starts_at_most_once`
      - $\neg var_i \lor \neg var_{i+1}$, for all $i$ in range $offset, offset + n - 1$
      - which creates pairs for negations of all variables, thus one of the clauses would fail in case of two starting indexes
 - it cannot overlap with other blocks withtin the same row (+ minimal spaces between blocks need to be satisfied) - function `no_two_blocks_overlap`
      - this was done in a similar way to the previous idea of paired negations, however, here, it is ensured that the next block cannot be placed before the previus one, nor during it, nor in at least one space after it (since separation of the block is needed) 

This was the "easier" part for the constraints. Then comes the part of placing the blocks based on columns.

#### Column Constraints
Here, the job is done through functions `min_filled_in_column`, `choose_filled_in_column` and `choose`. The names are not so descriptive and the functions themselves are less readable than the ones for rows. But, basic idea was to:
 - ensure the minimal placement exists based on the column rules, while sticking to the variables used for encoding row blocks
 - ensure that the number is exact according to the rule, while blocks need to stay consecutive

Unfortunately, my constraints do not always provide correct solution for the second option, which is of course an issue. However, one of the reasons I am turning in the work last minute is because I restarted the approach to the solution  about 6 different times, so at this point, this is the best I've got.

## User Documentation
The usage was kept the same as in [SAT Example](https://gitlab.mff.cuni.cz/svancaj/logika_SAT_example). So, basic usage:
```
nonogram.py [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]
```
Command-line options:
 - `-h`, `--help` : Show help message and exit
 - `-i INPUT`, `--input INPUT` : The instance file. Default: !!!??
 - `-o OUTPUT`, `--output OUTPUT` : Output file for the DIMACS format (i.e. the CNF formula)
 - `-s SOLVER`, `--solver SOLVER` : The SAT solver used. Default: glucose
 - `-v {0,1}`, `--verb {0,1}` : Verbosity of the SAT solver to be used
   
>[!WARNING]
>If you are planning on testing larger inputs on the [worse option](./inefficient_nonogram.py), I recommend getting yourself a coffee, extra disc and possibly a cooling fan (for both yourself and your PC) :slightly_smiling_face:

## Examples[^3]
 - [examples 2x2 grid](./examples/examples_2x2.txt)
 - [examples 3x3 grid](./examples/examples_3x3.txt)
 - [examples 4x4 grid](./examples/examples_4x4.txt)
 - [examples 5x5x grid](./examples/examples_5x5.txt)
 - [examples 6x6 grid](./examples/examples_6x6.txt)
 - [examples 7x7 grid](./examples/examples_7x7.txt)
 - [examples 10x10 grid](./examples/examples_10x10.txt)
 - [examples 15x15 grid](./examples/examples_15x15.txt)

## Experiments
This slightly strange experiment. But since I would like to fix my constraints so that they do not have flaws, I will try to do an evaluation of when the logic is broken.

The results are within the example files listed above
 - `w` next to input means that the programs compiled output was correct
 - `returns "UNSATISFIABLE"` means that the program nonogram.py collected incorrect result (inefficient_nonogram.py was correct in all cases, but time of computing was exponentially getting worse)
 - `expected output` is followed by `output` means that the solution provided was incorrect, both are inculded
 - `missplaces*` denotes the small incorrectness of the code, where the logic was broken by maximum of two rows/cols
 - `gets killed` means that the program never finished compiling

Overall the results are not ultimately conclusive, since for example simetry is an issue only sometimes, while other times it is computed correctly. The size of the grid, of course, becomes an issue pretty soon, however non-complex grids of larger sizes are still solved, while some 4x4 are not. The issue, I believe, lies within column constraints and their exact encoding. Frequency of issue `returns "UNSATISFIABLE"` , when the grid in fact has solution, might indicate that there is too many constraints. However, once I tried to simplfy them, it was not constrictive enough. 

### Sources and References
[^1]: https://liacs.leidenuniv.nl/~kosterswa/buffalo.pdf
[^2]: https://fse.studenttheses.ub.rug.nl/15287/1/Master_Educatie_2017_RAOosterman.pdf
[^3]: https://www.myhomeschoolmath.com/nonogram.html
