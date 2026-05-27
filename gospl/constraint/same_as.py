from typing import List

from .interface import Constraint
from gospl.variable import Variable


class SameAs(Constraint):
    variables: List[Variable]

    def __init__(self, var1: Variable, var2: Variable):
        self.variables = [var1, var2]

    def build(self, variable_qubits: List[List[int]], ancilla_qubits: List[int], signal_qubit: int) -> str:
        assert len(
            variable_qubits) == 2, f"SameAs constraint requires qubit ids for 2 variables. {len(variable_qubits)} were given."

        circuit = None

        for var1_qubit, var2_qubit in zip(variable_qubits[0], variable_qubits[1]):
            if circuit == None:
                circuit = f"CX({var1_qubit}, {var2_qubit})"
            else:
                circuit += f"\nCX({var1_qubit}, {var2_qubit})"

        gate = "C" * len(variable_qubits[1]) + "X("
        for var2_qubit in variable_qubits[1]:
            gate += f"{var2_qubit}, "  
        gate += f"{signal_qubit})"

        circuit += "\n" + gate
        return circuit

    @property
    def ancilla_count(self) -> int:
        return 0
