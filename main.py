from gospl.constraint import SameAs, Not
from gospl.variable import Variable
from gospl.builder import CircuitBuilder

if __name__ == "__main__":

    colors = ["red", "blue"]

    node1 = Variable(colors)
    node2 = Variable(colors)
    node3 = Variable(colors)

    Not(SameAs(node1, node2))
    Not(SameAs(node2, node3))

    builder = CircuitBuilder([node1, node2, node3])
    circuit = builder.build()

    print(circuit)