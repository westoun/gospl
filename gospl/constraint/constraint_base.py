from abc import ABC, abstractmethod
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List

from gospl.variable import Variable


class Constraint(ABC):
    variables: List[Variable]
    ancilla_count: int

    def __init__(self, variables: List[Variable]):
        self.variables = variables

        for variable in variables:
            variable.constraints.append(self)

    @abstractmethod
    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, signal_register: AncillaRegister, signal_qubit: int) -> None:
        ...

    @abstractmethod
    def __repr__(self):
        ...
