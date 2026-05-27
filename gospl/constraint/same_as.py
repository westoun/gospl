from typing import List

from .interface import Constraint
from gospl.variable import Variable
from gospl.utils import construct_mcx_gate, construct_cx_gate


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
                circuit = construct_cx_gate(var1_qubit, var2_qubit)
            else:
                circuit += "\n" + construct_cx_gate(var1_qubit, var1_qubit)

        circuit += "\n" + \
            construct_mcx_gate(
                control_qubits=variable_qubits[1], target_qubit=signal_qubit)
        return circuit

    @property
    def ancilla_count(self) -> int:
        return 0
