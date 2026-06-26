from abc import ABC, abstractmethod
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister, ClassicalRegister
from typing import List, Dict, Tuple

from gospl.variable import Variable
from gospl.constraint import Constraint, LessThan
from .utils import extract_constraints
from .builder_base import BuilderBase


def add_constraints_to_circuit(
    circuit: QuantumCircuit,
    variable_registers: List[QuantumRegister],
    ancilla_register: QuantumRegister,
    signal_register: QuantumRegister,
    variables: List[Variable], constraints: List[Constraint]
) -> None:

    used_ancillas = 0
    for constraint in constraints:

        variable_indices = [
            variables.index(variable) for variable in constraint.variables
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
            used_signal_qubits=0
        )

        circuit.cp(
            theta=np.pi / len(constraints),
            control_qubit=signal_register[0],
            target_qubit=signal_register[1]
        )

        # Uncompute after phase kickback.
        constraint.build(
            circuit,
            variable_registers=rel_variable_registers,
            ancilla_register=ancilla_register,
            used_ancillas=used_ancillas,
            signal_register=signal_register,
            used_signal_qubits=0
        )

        circuit.barrier()

        used_ancillas += constraint.ancilla_count


def prepare_kickback_qubit(circuit: QuantumCircuit,
                           signal_register: QuantumRegister) -> None:
    circuit.x(signal_register[1])


class SubPhaseCircuitBuilder(BuilderBase):
    def create_circuit(self) -> QuantumCircuit:
        constraints = extract_constraints(self.variables)
        print("Constraint count: " + str(len(constraints)))

        self.variable_registers = [
            QuantumRegister(variable.qubit_count, variable.name)
            for variable in self.variables
        ]

        total_ancilla_qubits = max(
            [constraint.ancilla_count for constraint in constraints])
        self.ancilla_register = AncillaRegister(
            total_ancilla_qubits, name="anc")

        self.signal_register = AncillaRegister(
            2, name="sig")

        self.classical_registers = [
            ClassicalRegister(variable.qubit_count, variable.name + "Cl")
            for variable in self.variables
        ]

        return QuantumCircuit(
            *self.variable_registers, self.ancilla_register, self.signal_register, *self.classical_registers)

    def add_oracle(self, circuit: QuantumCircuit) -> None:
        constraints = extract_constraints(self.variables)
        prepare_kickback_qubit(circuit, self.signal_register)
        add_constraints_to_circuit(circuit, self.variable_registers, self.ancilla_register, self.signal_register,
                                   self.variables, constraints)
