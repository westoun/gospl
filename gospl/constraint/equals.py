from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List, Any

from .constraint_base import Constraint
from gospl.variable import Variable


class Equals(Constraint):
    variables: List[Variable]
    value: Any

    def __init__(self, var: Variable, value: Any):
        super().__init__([var])
        self.value = value

    def build(self, circuit: QuantumCircuit, variable_registers: List[QuantumRegister], ancilla_register: AncillaRegister, used_ancillas: int, signal_register: AncillaRegister, used_signal_qubits: int) -> None:
        assert len(
            variable_registers) == 1, f"Is constraint requires qubit ids for 1 variable. {len(variable_registers)} were given."

        variable = self.variables[0]
        variable_register = variable_registers[0]

        try:
            int_value = variable.allowed.index(self.value)
        except ValueError:
            raise ValueError(
                f"'{self.value}' is not among the allowed values of variable '{variable.name}'.")

        bit_string = bin(int_value)[2:].zfill(len(variable_register))

        for bit_i, bit_value in enumerate(bit_string):

            if bit_value == "0":
                circuit.x(variable_register[bit_i])

        circuit.mcx(control_qubits=variable_register,
                    target_qubit=signal_register[used_signal_qubits])

        for bit_i, bit_value in enumerate(bit_string):

            if bit_value == "0":
                circuit.x(variable_register[bit_i])

    @property
    def ancilla_count(self) -> int:
        return 0

    def __repr__(self):
        return f"{self.variables[0].name} == {self.value}"