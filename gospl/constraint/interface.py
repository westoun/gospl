from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List

from gospl.variable import Variable


class Constraint:
    variables: List[Variable]
    ancilla_count: int

    def __init__(self, variables: List[Variable]):
        self.variables = variables

        for variable in variables:
            variable.constraints.append(self)

    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, used_ancillas: int, signal_register: AncillaRegister, used_signal_qubits: int) -> QuantumCircuit:
        raise NotImplementedError()
