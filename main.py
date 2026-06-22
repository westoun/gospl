from gospl.constraint import SameAs, Not, LessThan
from gospl.variable import Variable
from gospl.builder import CircuitBuilder

from qiskit.qasm3 import dumps

if __name__ == "__main__":

    colors = ["red", "green", "blue"]

    wa = Variable("Western Australia", colors)
    nt = Variable("Northern Territory", colors)
    sa = Variable("South Australia", colors)
    q = Variable("Queensland", colors)
    nsw = Variable("New South Wales", colors)
    v = Variable("Victoria", colors)
    t = Variable("Tasmania", colors)

    Not(SameAs(wa, nt))
    Not(SameAs(wa, sa))
    Not(SameAs(nt, q))
    Not(SameAs(nt, sa))
    Not(SameAs(sa, q))
    Not(SameAs(sa, nsw))
    Not(SameAs(q, nsw))
    Not(SameAs(sa, v))
    Not(SameAs(nsw, v))

    builder = CircuitBuilder([wa, nt, sa, q, nsw, v, t])

    circuit = builder.create_circuit()

    builder.add_oracle(circuit)

    print(circuit)
    print("Circuit depth: ", circuit.depth())
    print("Qubit count: ", circuit.width())

    gate_count = 0
    for gate, count in circuit.count_ops().items():
        gate_count += count

    print("Gate count: ", gate_count)

    qasm_circuit = dumps(circuit)
    with open("oracle.qasm", "w") as target_file:
        target_file.write(qasm_circuit)
