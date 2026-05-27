from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
from typing import List, Dict

from .variable import Variable
from .constraint import Constraint


def extract_constraints(variables: List[Variable]) -> List[Constraint]:
    constraints: List[Constraint] = []
    for variable in variables:

        # Add removal of invalid values constraint
        # for each variable.

        for constraint in variable.constraints:
            if constraint not in constraints:
                constraints.append(constraint)

    return constraints


class CircuitBuilder:
    variables: List[Variable]

    def __init__(self, variables: List[Variable]):
        self.variables = variables

    def build(self) -> QuantumCircuit:

        # If needed, add value constraint for each variable

        # Extract constraints from variables
        constraints = extract_constraints(self.variables)

        # Sort constraints to minimize depth

        # Determine total number of qubits
        variable_registers = [
            QuantumRegister(variable.qubit_count, variable.name)
            for variable in self.variables
        ]

        total_ancilla_qubits = sum(
            [constraint.ancilla_count for constraint in constraints])
        ancilla_register = AncillaRegister(
            total_ancilla_qubits, name="anc")

        total_signal_qubits = len(constraints) + 1
        signal_register = AncillaRegister(
            total_signal_qubits, name="sig")

        circuit = QuantumCircuit(
            *variable_registers, ancilla_register, signal_register)

        used_ancillas = 0
        used_signal_qubits = 0
        for constraint in constraints:

            variable_indices = [
                self.variables.index(variable) for variable in constraint.variables
            ]

            rel_variable_registers = [
                variable_registers[variable_index]
                for variable_index in variable_indices
            ]

            constraint.build(
                circuit,
                variable_registers=rel_variable_registers,
                ancilla_register=ancilla_register,
                used_ancillas=used_ancillas,
                signal_register=signal_register,
                used_signal_qubits=used_signal_qubits
            )

            used_ancillas += constraint.ancilla_count
            used_signal_qubits += 1

        circuit.mcx(control_qubits=signal_register[:-1], target_qubit=signal_register[-1])

        # uncompute circuit

        return circuit
