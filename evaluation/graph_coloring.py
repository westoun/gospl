import click
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

from gospl.constraint import SameAs, Not, LessThan, Equals
from gospl.variable import Variable
from gospl.circuit_builder import CircuitBuilder
from utils import save_to_json, get_timestamp, count_gates


def encode_graph(adjaceny_matrix: List, colors: List) -> List[Variable]:
    nodes = []
    for i in range(len(adjaceny_matrix)):
        node = Variable(f"Node{i+1}", colors)
        nodes.append(node)

    for i in range(len(adjaceny_matrix)):

        # Avoid self references or double counting of relationships
        # due to undirectedness of edges.
        for j in range(i + 1, len(adjaceny_matrix)):

            if adjaceny_matrix[i][j] == 1:
                Not(SameAs(nodes[i], nodes[j]))
    return nodes


def initialize_graph(node_count: int, edge_count: int) -> List[List[int]]:
    potential_edges = []

    for node1_i in range(node_count):
        for node2_i in range(node1_i + 1, node_count):
            potential_edges.append(f"({node1_i}, {node2_i})")

    selected_edges = random.sample(potential_edges, edge_count)

    adjacency_matrix = []
    for row_i in range(node_count):
        adjacency_matrix.append([])

        for col_i in range(node_count):

            if f"({row_i}, {col_i})" in selected_edges:
                adjacency_matrix[-1].append(1)
            elif f"({col_i}, {row_i})" in selected_edges:
                adjacency_matrix[-1].append(1)
            else:
                adjacency_matrix[-1].append(0)

    return adjacency_matrix


def count_constraint_violations(adjaceny_matrix: List, node_colors: List[str]) -> int:
    constraint_violations = 0

    for node_color in node_colors:
        if node_color == "N/A":
            constraint_violations += 1

    for node1_i, node1_color in enumerate(node_colors):

        for node2_i, node2_color in enumerate(node_colors):
            if node2_i <= node1_i:
                continue

            if adjaceny_matrix[node1_i][node2_i] == 1 and node1_color == node2_color:
                constraint_violations += 1

    return constraint_violations


@click.command()
@click.option(
    "--nodes",
    "-n",
    "node_count",
    type=click.INT,
    default=4
)
@click.option(
    "--edges",
    "-e",
    "edge_count",
    type=click.INT,
    default=3
)
@click.option(
    "--colors",
    "-c",
    "color_count",
    type=click.INT,
    default=3
)
@click.option(
    "--ancilla-qubits",
    "-a",
    "ancilla_qubits",
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
def run_graph_coloring_experiment(node_count: int, edge_count: int, color_count: int, ancilla_qubits: int,
                                  store_circuit: bool, seed: int, tag: str):
    colors = ["red", "green", "blue", "yellow", "purple", "black",
              "white", "orange", "pink", "brown", "magenta", "cyan"]

    assert color_count <= len(
        colors), f"At the moment, only support color counts up to {len(colors)}."
    colors = colors[:color_count]

    max_connections = node_count * (node_count - 1) / 2
    assert edge_count <= max_connections, f"For {node_count} nodes, the maximum number of possible edges is {max_connections} (not {edge_count})."

    shots = 100_000
    shot_threshold = int(0.001 * shots)

    experiment_prefix = f"graph_coloring_{node_count}n_{edge_count}e_{color_count}c_{ancilla_qubits}a{get_timestamp()}"

    data = {
        "meta": {
            "experiment_prefix": experiment_prefix,
            "tag": tag,
            "timestamp": get_timestamp()
        },
        "params": {
            "node_count": node_count,
            "edge_count": edge_count,
            "color_count": color_count,
            "ancilla_qubits": ancilla_qubits,
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
            "depth": None,
        },
        "results": []
    }

    random.seed(seed)
    np_random.seed(seed)

    adjaceny_matrix = initialize_graph(node_count, edge_count)
    data["problem_instance"] = adjaceny_matrix

    nodes = encode_graph(adjaceny_matrix, colors)

    builder = CircuitBuilder(nodes, signal_qubits=ancilla_qubits)

    circuit = builder.create_circuit()

    builder.add_h_layer(circuit)
    builder.add_oracle(circuit)
    builder.add_diffusion(circuit)

    builder.add_measurement(circuit)
    if store_circuit:
        circuit.draw(output='mpl', filename=f"results/{experiment_prefix}.png",
                     vertical_compression=None)

    circuit = RemoveBarriers()(circuit)

    data["encoding"]["variables"] = len(nodes)
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

    for solution, count in counts.items():

        if count < shot_threshold:
            continue

        # Reverse measurement bit order as qiskit seems to index bottom up.
        solution = solution[::-1]

        node_colors = []
        for register_value in solution.split():
            index = int(register_value, 2)

            if index >= len(colors):
                node_colors.append("N/A")
            else:
                node_colors.append(colors[index])

        violations = count_constraint_violations(
            adjaceny_matrix, node_colors)

        probability = count / shots

        if violations not in results_per_constraint_violation:
            results_per_constraint_violation[violations] = {
                "probabilities": [probability],
                "solutions": [node_colors]
            }
        else:
            results_per_constraint_violation[violations]["probabilities"].append(
                probability)
            results_per_constraint_violation[violations]["solutions"].append(
                node_colors)

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
    run_graph_coloring_experiment()
