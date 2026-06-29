import math
import os
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile
from qiskit.transpiler.passes import RemoveBarriers
import sys
sys.path.append(os.path.abspath('..'))  # nopep8
from typing import List

from gospl.constraint import SameAs, Not, LessThan, Equals
from gospl.variable import Variable
from gospl.builder import SubPhaseCircuitBuilder, CircuitBuilder, TunableBuilder


def print_sudoku(sudoku: List[List]):
    for i, row in enumerate(sudoku):

        if i % 2 == 0:
            print("# # # # # # #")

        values = []
        for value in row:
            if value is None:
                values.append(" ")
            else:
                values.append(value)

        print(f"# {values[0]} {values[1]} # {values[2]} {values[3]} #")

    print("# # # # # # #")


def find_variable(variables: List[Variable], row_i: int, col_i: int) -> Variable:
    target_name = f"Cell{row_i},{col_i}"

    for variable in variables:
        if variable.name == target_name:
            return variable

    raise ValueError(f"No variable found for target name '{target_name}'")


def print_filled_sudoku(sudoku: List[List], cell_values: List[int]) -> None:

    used_cells = 0

    for i, row in enumerate(sudoku):

        if i % 2 == 0:
            print("# # # # # # #")

        values = []
        for value in row:
            if value is None:
                values.append(f"\033[96m{cell_values[used_cells]}\033[0m")
                used_cells += 1
            else:
                values.append(value)

        print(f"# {values[0]} {values[1]} # {values[2]} {values[3]} #")

    print("# # # # # # #")


if __name__ == "__main__":

    # sudoku = [
    #     [1, 2, None, 4],
    #     [4, 3, None, 1],
    #     [3, None, 1, 2],
    #     [2, 1, 4, 3]
    # ]
    sudoku = [
        [1, 3, 4, None],
        [4, 2, None, 3],
        [None, 1, 3, 4],
        [3, 4, None, 1]
    ]
    print_sudoku(sudoku)

    numbers = [1, 2, 3, 4]
    variables: List[Variable] = []

    for row_i, row in enumerate(sudoku):
        for col_i, cell in enumerate(row):

            if cell is not None:
                continue

            variable = Variable(
                f"Cell{row_i},{col_i}", numbers
            )

            variables.append(variable)

    for variable in variables:
        coordinates = variable.name.replace("Cell", "").split(",")
        row = int(coordinates[0])
        col = int(coordinates[1])

        constraint_values = []

        # Add constraints for entries in same row
        for col_i in range(len(sudoku)):
            if sudoku[row][col_i] is not None:
                constraint_values.append(sudoku[row][col_i])
            elif col_i > col:
                variable2 = find_variable(variables, row, col_i)
                constraint_values.append(variable2)

        # Add constraints for entries in same column
        for row_i in range(len(sudoku)):
            if sudoku[row_i][col] is not None:
                constraint_values.append(sudoku[row_i][col])
            elif row_i > row:
                variable2 = find_variable(variables, row_i, col)
                constraint_values.append(variable2)

        # Add constraints for each block
        block_width = int(math.sqrt(len(sudoku)))
        start_row = math.floor(row / block_width) * block_width
        start_col = math.floor(col / block_width) * block_width
        for row_i in range(start_row, start_row + block_width):

            # Already covered by same row constraint
            if row_i == row:
                continue

            for col_i in range(start_col, start_col + block_width):

                # Already covered by same col constraint
                if col_i == col:
                    continue

                if sudoku[row_i][col_i] is not None:
                    constraint_values.append(sudoku[row_i][col_i])
                elif row_i > row:
                    variable2 = find_variable(variables, row_i, col_i)
                    constraint_values.append(variable2)

        # Remove duplicates
        constraint_values = list(set(constraint_values))

        for value in constraint_values:
            if type(value) == Variable:
                Not(SameAs(variable, value))
            else:
                Not(Equals(variable, value))

    builder = TunableBuilder(variables, buffer_qubits=5)

    circuit = builder.create_circuit()

    builder.add_h_layer(circuit)
    builder.add_oracle(circuit)
    builder.add_diffusion(circuit)

    builder.add_measurement(circuit)

    circuit.draw(output='mpl', filename='sudoku_circuit.png',
                 vertical_compression=None)

    circuit = RemoveBarriers()(circuit)

    print("Circuit depth: ", circuit.depth())
    print("Qubit count: ", circuit.width())

    gate_count = 0
    for gate, count in circuit.count_ops().items():
        gate_count += count

    print("Gate count: ", gate_count)

    simulator = AerSimulator()

    shots = 50_000

    job = simulator.run(transpile(circuit, simulator), shots=shots)
    result = job.result()

    counts = result.get_counts(circuit)

    for solution, count in sorted(counts.items(), key=lambda item: -item[1])[:5]:

        # Reverse measurement bit order as qiskit seems to index bottom up.
        solution = solution[::-1]

        if count < 0.005 * shots:
            continue

        solutions = []

        for register_value in solution.split():
            index = int(register_value, 2)
            solutions.append(str(numbers[index]))

        print("")
        print_filled_sudoku(sudoku, cell_values=solutions)

        solution = " - ".join(solutions)

        print(f"{solution}: {count} ({round(count / shots * 100, 2)}%)")
