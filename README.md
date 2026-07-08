# GOSPL

This repository contains the source code to the paper
_"A Constraint-Based DSL for the Automatic Generation of Grover Oracles"_
by Stein, Klikovits, and Wimmer from the [Institute of Business Informatics - Software Engineering](https://se.jku.at/) at the [Johannes Kepler University](https://www.jku.at/en), Linz
and Schenkenfelder from the [Software Competence Center Hagenberg](https://www.scch.at/).
The `evaluation/` directory contains the code used in the evaluation section of the 
paper.


## Installation

To use GOSPL, download the repository and use the package manager
[pip](https://pip.pypa.io/en/stable/) to install the needed requirements

```bash
pip install -r requirements.txt
```

## Usage

GOSPL (Grover Oracle Specific Programming Language) is a declarative programming language that 
enables its user to develop Grover oracle for constraint satisfaction problems without any 
knowledge of quantum gates and qubits.

The following code snippet shows how GOSPL can be used to derive an
oracle circuit for the [map/graph coloring problem](https://en.wikipedia.org/wiki/Graph_coloring) of the [territories of Australia](https://en.wikipedia.org/wiki/States_and_territories_of_Australia).

```python
from gospl.constraint import SameAs, Not
from gospl.variable import Variable
from gospl.builder import CircuitBuilder

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
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
