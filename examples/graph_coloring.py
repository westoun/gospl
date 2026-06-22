import os

import sys
sys.path.append(os.path.abspath('..'))  # nopep8

from gospl.constraint import SameAs, Not, LessThan, Equals
from gospl.variable import Variable
from gospl.builder import CircuitBuilder

from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from qiskit import transpile
from qiskit.circuit.library import HGate

if __name__ == "__main__":

    colors = ["red", "green", "blue"]

    node1 = Variable("Node1", colors)
    node2 = Variable("Node2", colors)
    node3 = Variable("Node3", colors)

    Not(SameAs(node1, node2))
    Not(SameAs(node1, node3))
    Not(SameAs(node2, node3))

    builder = CircuitBuilder([node1, node2, node3])

    variable_registers, ancilla_register, signal_register = builder.initialize_registers()
    circuit = builder.create_circuit(variable_registers, ancilla_register, signal_register)

    for variable_register in variable_registers:
        circuit.h(variable_register)

    builder.add_oracle(circuit)

    print("Circuit depth: ", circuit.depth())
    print("Qubit count: ", circuit.width())

    gate_count = 0
    for gate, count in circuit.count_ops().items():
        gate_count += count 

    print("Gate count: ", gate_count)

    circuit.draw(output='mpl', filename='circuit.png', vertical_compression=None)

    circuit.save_statevector()
    simulator = AerSimulator(method='statevector')

    job = simulator.run(circuit)
    result = job.result()
    statevector = result.get_statevector(circuit)

    # 4. Print the resulting amplitudes
    for i, entry in enumerate(statevector.data):
        # print(entry)
        if abs(entry) > 0.01 and entry.real < 0:
            print(i) 