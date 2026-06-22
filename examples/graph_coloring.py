import os

import sys
sys.path.append(os.path.abspath('..'))  # nopep8

from matplotlib import pyplot as plt
from typing import List

from gospl.constraint import SameAs, Not, LessThan, Equals
from gospl.variable import Variable
from gospl.builder import CircuitBuilder
from qiskit.compiler import transpile

from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

if __name__ == "__main__":

    colors = ["red", "green", "blue"]

    node1 = Variable("Node1", colors)
    node2 = Variable("Node2", colors)
    node3 = Variable("Node3", colors)

    Not(SameAs(node1, node2))
    Not(SameAs(node1, node3))
    Not(SameAs(node2, node3))

    builder = CircuitBuilder([node1, node2, node3])

    circuit = builder.create_circuit()

    builder.add_h_layer(circuit)
    builder.add_oracle(circuit)
    builder.add_diffusion(circuit)
    builder.add_measurement(circuit)

    print("Circuit depth: ", circuit.depth())
    print("Qubit count: ", circuit.width())

    gate_count = 0
    for gate, count in circuit.count_ops().items():
        gate_count += count

    print("Gate count: ", gate_count)

    circuit.draw(output='mpl', filename='circuit.png',
                 vertical_compression=None)

    simulator = AerSimulator()

    shots = 10_000
    job = simulator.run(transpile(circuit, simulator), shots=shots)
    result = job.result()

    counts = result.get_counts(circuit)

    for solution, count in counts.items():
        if count > 0.01 * shots:
            print(f"{solution}: {count}")

    # plot_histogram(counts)
    # plt.show()
