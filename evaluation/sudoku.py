import click
import math
from numpy import random as np_random
import os
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile
from qiskit.transpiler.passes import RemoveBarriers
import random
from statistics import mean, stdev
import sys
sys.path.append(os.path.abspath('..'))  # nopep8
from typing import List
from uuid import uuid4

from gospl.constraint import SameAs, Not, LessThan, Equals
from gospl.variable import Variable
from gospl.circuit_builder import CircuitBuilder
from utils import save_to_json, get_timestamp, count_gates


def stringify_sudoku(sudoku: List[List]) -> str:
    repr = ""

    for i, row in enumerate(sudoku):

        if i % 2 == 0:
            repr += "# # # # # # #\n"

        values = []
        for value in row:
            if value is None:
                values.append(" ")
            else:
                values.append(value)

        repr += f"# {values[0]} {values[1]} # {values[2]} {values[3]} #\n"

    repr += "# # # # # # #"
    return repr


def print_sudoku(sudoku: List[List]):
    print(stringify_sudoku(sudoku))


def find_variable(variables: List[Variable], row_i: int, col_i: int) -> Variable:
    target_name = f"Cell{row_i},{col_i}"

    for variable in variables:
        if variable.name == target_name:
            return variable

    raise ValueError(f"No variable found for target name '{target_name}'")


def stringify_filled_sudoku(sudoku: List[List], cell_values: List[int]) -> str:
    repr = ""

    used_cells = 0

    for i, row in enumerate(sudoku):

        if i % 2 == 0:
            repr += "# # # # # # #\n"

        values = []
        for value in row:
            if value is None:
                values.append(f"\033[96m{cell_values[used_cells]}\033[0m")
                used_cells += 1
            else:
                values.append(value)

        repr += f"# {values[0]} {values[1]} # {values[2]} {values[3]} #\n"

    repr += "# # # # # # #"
    return repr


def print_filled_sudoku(sudoku: List[List], cell_values: List[int]) -> None:
    print(stringify_filled_sudoku(sudoku, cell_values))


def encode_sudoku(sudoku: List[List]) -> List[Variable]:
    numbers = [i + 1 for i in range(len(sudoku))]
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

    return variables


def initialize_sudoku(variable_count: int) -> List[List[int]]:
    sudoku = [
        [1, 3, 4, 2],
        [4, 2, 1, 3],
        [2, 1, 3, 4],
        [3, 4, 2, 1]
    ]

    dim = len(sudoku)

    variable_indices = random.sample(range(dim * dim), variable_count)

    for variable_index in variable_indices:
        row = int(variable_index / dim)
        col = variable_index % dim

        sudoku[row][col] = None

    return sudoku


def count_constraint_violations(sudoku: List[List], variables: List[Variable], cell_values: List[int]) -> int:
    assert len(variables) == len(cell_values)

    constraint_violations = 0

    for variable_i, variable in enumerate(variables):
        coordinates = variable.name.replace("Cell", "").split(",")
        row = int(coordinates[0])
        col = int(coordinates[1])

        constraint_values = []
        constraint_variable_indices = []

        # Add constraints for entries in same row
        for col_i in range(len(sudoku)):
            if sudoku[row][col_i] is not None:
                constraint_values.append(sudoku[row][col_i])
            elif col_i > col:
                variable2 = find_variable(variables, row, col_i)
                constraint_variable_indices.append(variables.index(variable2))

        # Add constraints for entries in same column
        for row_i in range(len(sudoku)):
            if sudoku[row_i][col] is not None:
                constraint_values.append(sudoku[row_i][col])
            elif row_i > row:
                variable2 = find_variable(variables, row_i, col)
                constraint_variable_indices.append(variables.index(variable2))

        # Add constraints for entries in same block
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
                    constraint_variable_indices.append(
                        variables.index(variable2))

        constraint_values = list(set(constraint_values))
        if cell_values[variable_i] in constraint_values:
            constraint_violations += 1

        constraint_variable_indices = list(set(constraint_variable_indices))
        for constraint_variable_index in constraint_variable_indices:
            if cell_values[variable_i] == cell_values[constraint_variable_index]:
                constraint_violations += 1

    return constraint_violations


@click.command()
@click.option(
    "--variables",
    "-v",
    "variable_count",
    type=click.INT,
    default=4
)
@click.option(
    "--buffer-qubits",
    "-bq",
    "buffer_qubits",
    type=click.INT,
    default=None
)
@click.option(
    "--store-circuit",
    "-sc",
    "store_circuit",
    type=click.BOOL,
    default=False
)
@click.option(
    "--seed",
    "-s",
    "seed",
    type=click.INT,
    default=0
)
@click.option(
    "--tag",
    "-t",
    "tag",
    type=click.STRING,
    default=None
)
def run_sudoku_experiment(variable_count: int, buffer_qubits: int, store_circuit: bool, seed: int, tag: str):
    assert variable_count <= 16, "Cannot have more variables than cells in the sudoku (16)."

    shots = 100_000
    shot_threshold = int(0.001 * shots)

    experiment_prefix = f"sudoku_{variable_count}v_{buffer_qubits}b_{get_timestamp()}"

    data = {
        "meta": {
            "experiment_prefix": experiment_prefix,
            "tag": tag,
            "timestamp": get_timestamp()
        },
        "params": {
            "variable_count": variable_count,
            "buffer_qubits": buffer_qubits,
            "store_circuit": store_circuit,
            "seed": seed,
            "shots": shots,
            "shot_threshold": shot_threshold,
        },
        "problem_instance": None,
        "encoding": {
            "variables": None,
            "constraints": None,
            "qubits": None,
            "gates": None,
            "depth": None
        },
        "results": []
    }

    random.seed(seed)
    np_random.seed(seed)

    sudoku = initialize_sudoku(variable_count)
    data["problem_instance"] = sudoku

    variables = encode_sudoku(sudoku)

    builder = CircuitBuilder(variables, buffer_qubits=buffer_qubits)

    circuit = builder.create_circuit()

    builder.add_h_layer(circuit)
    builder.add_oracle(circuit)
    builder.add_diffusion(circuit)

    builder.add_measurement(circuit)

    if store_circuit:
        circuit.draw(output='mpl', filename=f"results/{experiment_prefix}.png",
                     vertical_compression=None)

    circuit = RemoveBarriers()(circuit)

    data["encoding"]["variables"] = len(variables)
    data["encoding"]["constraints"] = len(builder.constraints)
    data["encoding"]["qubits"] = circuit.width()
    data["encoding"]["gates"] = count_gates(circuit)
    data["encoding"]["depth"] = circuit.depth()

    simulator = AerSimulator(seed_simulator=seed)

    job = simulator.run(transpile(circuit, simulator,
                        seed_transpiler=seed), shots=shots)
    result = job.result()
    counts = result.get_counts(circuit)

    results_per_constraint_violation = {}

    for solution, count in sorted(counts.items(), key=lambda item: -item[1])[:5]:

        if count < shot_threshold:
            continue

        # Reverse measurement bit order as qiskit seems to index bottom up.
        solution = solution[::-1]

        cell_values = []
        for register_value in solution.split():
            index = int(register_value, 2)
            cell_values.append(index + 1)

        violations = count_constraint_violations(
            sudoku, variables, cell_values)

        probability = count / shots

        if violations not in results_per_constraint_violation:
            results_per_constraint_violation[violations] = {
                "probabilities": [probability],
                "solutions": [cell_values]
            }
        else:
            results_per_constraint_violation[violations]["probabilities"].append(
                probability)
            results_per_constraint_violation[violations]["solutions"].append(
                cell_values)

    for violations in sorted(results_per_constraint_violation.keys()):
        probabilities = results_per_constraint_violation[violations]["probabilities"]
        solutions = results_per_constraint_violation[violations]["solutions"]

        # Avoid statistics error during variance computation
        if len(solutions) == 1:
            data["results"].append({
                "constraint_violations": violations,
                "solutions": solutions[:3],
                "state_count": 1,
                "mean_prob": probabilities[0],
                "std_prob": None
            })

        else:
            data["results"].append({
                "constraint_violations": violations,
                "solutions": solutions[:3],
                "state_count": len(solutions),
                "mean_prob": mean(probabilities),
                "std_prob": stdev(probabilities)
            })

    save_to_json(data, path=f"results/{experiment_prefix}.json")


if __name__ == "__main__":
    run_sudoku_experiment()
