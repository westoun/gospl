from typing import List

from .interface import Constraint
from gospl.variable import Variable


class Not(Constraint):
    variables: List[Variable]
    constraint: Constraint

    def __init__(self, constraint: Constraint):
        for variable in constraint.variables:

            # Remove existing linking to avoid confusion during
            # circuit building.
            if constraint in constraint.variables:
                constraint.variables.remove(constraint)

            variable.constraints.append(self)

        self.variables = constraint.variables
        self.constraint = constraint

    def build(self, variable_qubits: List[int], ancilla_qubits: List[int], signal_qubit: int) -> str:
        circuit = f"X({signal_qubit})"
        circuit += "\n" + self.constraint.build(
            variable_qubits, ancilla_qubits, signal_qubit
        )
        return circuit

    @property
    def ancilla_count(self) -> int:
        return self.constraint.ancilla_count
