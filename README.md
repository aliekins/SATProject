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

## Encoding
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

## Examples
examples here

## Experiments
experiment here
### Sources and References
[^1]: My source
