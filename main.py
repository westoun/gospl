from gospl.constraint import SameAs, Not, LessThan
from gospl.variable import Variable
from gospl.builder import CircuitBuilder

from qiskit.qasm3 import dumps

if __name__ == "__main__":

    colors = ["red", "blue", "green"]

    node1 = Variable("node_1", colors)
    node2 = Variable("node_2", colors)
    node3 = Variable("node_3", colors)
    node4 = Variable("node_4", colors)

    Not(SameAs(node1, node2))
    Not(SameAs(node2, node3))
    Not(SameAs(node2, node4))
    Not(SameAs(node3, node4))

    builder = CircuitBuilder([node1, node2, node3, node4])
    circuit = builder.build()

    print(circuit)
    print("Circuit depth: ", circuit.depth())
    print("Qubit count: ", circuit.width())

    qasm_circuit = dumps(circuit)
    with open("oracle.qasm", "w") as target_file:
        target_file.write(qasm_circuit)
