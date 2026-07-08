from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List

from .constraint_base import Constraint
from gospl.variable import Variable


class SameAs(Constraint):
    variables: List[Variable]

    def __init__(self, var1: Variable, var2: Variable):
        super().__init__([var1, var2])

    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, signal_register: AncillaRegister, signal_qubit: int) -> None:
        assert len(
            variable_registers) == 2, f"SameAs constraint requires qubit ids for 2 variables. {len(variable_registers)} were given."

        circuit.x(variable_registers[1])
        circuit.cx(variable_registers[0], variable_registers[1])

        circuit.mcx(
            control_qubits=variable_registers[1], target_qubit=signal_register[signal_qubit])

        circuit.x(variable_registers[1])
        circuit.cx(variable_registers[0], variable_registers[1])

    @property
    def ancilla_count(self) -> int:
        return 0

    def __repr__(self):
        return f"{self.variables[0].name} == {self.variables[1].name}"
