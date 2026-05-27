from typing import List

from gospl.variable import Variable


class Constraint:
    variables: List[Variable]
    ancilla_count: int

    def __init__(self, variables: List[Variable]):
        self.variables = variables

        for variable in variables:
            variable.constraints.append(self)

    def build(self, variable_qubits: List[List[int]], ancilla_qubits: List[int], signal_qubit: int) -> str:
        raise NotImplementedError()
