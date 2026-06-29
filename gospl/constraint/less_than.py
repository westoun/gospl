from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List

from .constraint_base import Constraint
from gospl.variable import Variable


class LessThan(Constraint):
    variables: List[Variable]
    value: int

    def __init__(self, variable: Variable, value: int):
        super().__init__([variable])
        self.value = value

    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, used_ancillas: int, signal_register: AncillaRegister, used_signal_qubits: int) -> None:
        assert len(
            variable_registers) == 1, f"LessThan constraint requires qubit ids for exactly 1 variable. {len(variable_registers)} were given."

        variable_register = variable_registers[0]

        bit_string = bin(self.value)[2:].zfill(len(variable_register))

        for bit_i, bit_value in enumerate(bit_string):
            circuit.x(variable_register[bit_i])

            if bit_value == "1":
                control_qubits = variable_register[: bit_i + 1]
                circuit.mcx(
                    control_qubits=control_qubits, target_qubit=signal_register[used_signal_qubits])
                circuit.x(variable_register[bit_i])

        for bit_i, bit_value in enumerate(bit_string):
            if bit_value == "0":
                circuit.x(variable_register[bit_i])

    @property
    def ancilla_count(self) -> int:
        return 0

    def __repr__(self):
        return f"{self.variables[0].name} < {self.value}"
