from abc import ABC, abstractmethod
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister, ClassicalRegister
from typing import List, Dict, Tuple

from gospl.variable import Variable
from gospl.constraint import Constraint, LessThan


def add_allowed_value_constraints(variables: List[Variable]) -> None:
    for variable in variables:
        if 2 ** variable.qubit_count > len(variable.allowed):
            LessThan(variable, len(variable.allowed))


class BuilderBase(ABC):
    variables: List[Variable]
    variable_registers: List[QuantumRegister]
    ancilla_register: QuantumRegister
    signal_register: QuantumRegister
    classical_registers: List[ClassicalRegister]

    def __init__(self, variables: List[Variable]):
        self.variables = variables
        add_allowed_value_constraints(self.variables)

    @abstractmethod
    def create_circuit(self) -> QuantumCircuit:
        ...

    def add_h_layer(self, circuit: QuantumCircuit) -> None:
        for variable_register in self.variable_registers:
            circuit.h(variable_register)
        circuit.barrier()

    @abstractmethod
    def add_oracle(self, circuit: QuantumCircuit) -> None:
        ...

    def add_diffusion(self, circuit: QuantumCircuit) -> None:
        for variable_register in self.variable_registers:
            circuit.h(variable_register)
            circuit.x(variable_register)

        # Inspired by https://qiskit.qotlabs.org/learning/courses/utility-scale-quantum-computing/grovers-algorithm#3-diffusion-operator

        qubit_count = sum(
            [register.size for register in self.variable_registers])

        circuit.h(qubit_count - 1)
        circuit.mcx([i for i in range(0, qubit_count - 1)], qubit_count - 1)
        circuit.h(qubit_count - 1)

        for variable_register in self.variable_registers:
            circuit.x(variable_register)
            circuit.h(variable_register)

        circuit.barrier()

    def add_measurement(self, circuit: QuantumCircuit) -> None:

        for variable_register, classical_register in zip(self.variable_registers, self.classical_registers):
            circuit.measure(variable_register, classical_register)
