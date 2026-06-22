from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List

from .interface import Constraint
from gospl.variable import Variable


class SameAs(Constraint):
    variables: List[Variable]

    def __init__(self, var1: Variable, var2: Variable):
        super().__init__([var1, var2])

    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, used_ancillas: int, signal_register: AncillaRegister, used_signal_qubits: int) -> QuantumCircuit:
        assert len(
            variable_registers) == 2, f"SameAs constraint requires qubit ids for 2 variables. {len(variable_registers)} were given."

        circuit.x(variable_registers[1])
        circuit.cx(variable_registers[0], variable_registers[1])

        circuit.mcx(
            control_qubits=variable_registers[1], target_qubit=signal_register[used_signal_qubits])

        circuit.x(variable_registers[1])
        circuit.cx(variable_registers[0], variable_registers[1])
        return circuit

    @property
    def ancilla_count(self) -> int:
        return 0
