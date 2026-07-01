import os
from qiskit_aer import AerSimulator
from qiskit.compiler import transpile
from qiskit.transpiler.passes import RemoveBarriers
import sys
sys.path.append(os.path.abspath('..'))  # nopep8
from typing import List

from gospl.constraint import SameAs, Not, LessThan, Equals
from gospl.variable import Variable
from gospl.circuit_builder import CircuitBuilder


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


if __name__ == "__main__":

    colors = ["red", "green", "blue"]

    adjaceny_matrix = [
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0]
    ]

    nodes = encode_graph(adjaceny_matrix, colors)

    builder = CircuitBuilder(nodes, buffer_qubits=3)

    circuit = builder.create_circuit()

    builder.add_h_layer(circuit)
    builder.add_oracle(circuit)
    builder.add_diffusion(circuit)

    builder.add_measurement(circuit)

    circuit.draw(output='mpl', filename='graph_coloring_circuit.png',
                 vertical_compression=None)

    circuit = RemoveBarriers()(circuit)

    print("")
    print("Constraint count: ", len(builder.constraints))
    print("Circuit depth: ", circuit.depth())
    print("Qubit count: ", circuit.width())

    gate_count = 0
    for gate, count in circuit.count_ops().items():
        gate_count += count

    print("Gate count: ", gate_count)

    simulator = AerSimulator()

    shots = 10_000
    job = simulator.run(transpile(circuit, simulator), shots=shots)
    result = job.result()

    counts = result.get_counts(circuit)

    for solution, count in counts.items():

        solution = solution[::-1]

        if count < 0.01 * shots:
            continue

        solutions = []

        for register_value in solution.split():
            index = int(register_value, 2)

            if index >= len(colors):
                solutions.append("N/A")
            else:
                solutions.append(colors[index])

        solution = " - ".join(solutions)

        print(f"{solution}: {count} ({round(count / shots * 100, 2)}%)")
