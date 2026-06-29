from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List

from .constraint_base import Constraint
from gospl.variable import Variable


class Not(Constraint):
    variables: List[Variable]
    constraint: Constraint

    def __init__(self, constraint: Constraint):
        for variable in constraint.variables:

            # Remove existing linking to avoid confusion during
            # circuit building.
            if constraint in variable.constraints:
                variable.constraints.remove(constraint)

            variable.constraints.append(self)

        self.variables = constraint.variables
        self.constraint = constraint

    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, used_ancillas: int, signal_register: AncillaRegister, used_signal_qubits: int) -> None:
        circuit.x(signal_register[used_signal_qubits])
        self.constraint.build(
            circuit, variable_registers, ancilla_register, used_ancillas, signal_register, used_signal_qubits
        )

    @property
    def ancilla_count(self) -> int:
        return self.constraint.ancilla_count

    def __repr__(self):
        return f"not {self.constraint}"
