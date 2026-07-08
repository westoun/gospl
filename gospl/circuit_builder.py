import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister, ClassicalRegister
from typing import List, Dict, Tuple

from gospl.variable import Variable
from gospl.constraint import Constraint, LessThan
from .utils import extract_constraints


class CircuitBuilder:
    variables: List[Variable]
    constraints: List[Constraint]

    variable_registers: List[QuantumRegister]
    ancilla_register: QuantumRegister
    signal_register: QuantumRegister
    classical_registers: List[ClassicalRegister]

    signal_qubits: int

    def __init__(self, variables: List[Variable], signal_qubits: int = None):
        for variable in variables:
            if 2 ** variable.qubit_count > len(variable.allowed):
                LessThan(variable, len(variable.allowed))

        self.variables = variables

        self.constraints = extract_constraints(variables)

        if signal_qubits is None:
            print(
                f"Setting signal qubits to number of constraints ({len(self.constraints)}).")
            signal_qubits = len(self.constraints)

        elif signal_qubits < 1:
            print(
                f"Invalid number of signal qubits specified ({signal_qubits}). Setting to number of constraints ({len(self.constraints)}).")
            signal_qubits = len(self.constraints)

        elif signal_qubits > len(self.constraints):
            print(
                f"More signal qubits provided than constraints ({signal_qubits} > {len(self.constraints)}). Setting signal qubits to number of constraints.")
            signal_qubits = len(self.constraints)

        self.signal_qubits = signal_qubits

    def create_circuit(self) -> QuantumCircuit:
        self.variable_registers = [
            QuantumRegister(variable.qubit_count, variable.name)
            for variable in self.variables
        ]

        total_ancilla_qubits = max(
            [constraint.ancilla_count for constraint in self.constraints])
        self.ancilla_register = AncillaRegister(
            total_ancilla_qubits, name="anc")

        self.signal_register = AncillaRegister(
            self.signal_qubits, name="sig")

        self.classical_registers = [
            ClassicalRegister(variable.qubit_count, variable.name + "Cl")
            for variable in self.variables
        ]

        return QuantumCircuit(
            *self.variable_registers, self.ancilla_register, self.signal_register, *self.classical_registers)

    def add_h_layer(self, circuit: QuantumCircuit) -> None:
        for variable_register in self.variable_registers:
            circuit.h(variable_register)
        circuit.barrier()

    def add_oracle(self, circuit: QuantumCircuit) -> None:
        added_constraints = 0

        buffer_rounds = math.floor(len(self.constraints) / self.signal_qubits)
        for _ in range(buffer_rounds):

            for i in range(self.signal_qubits):
                constraint = self.constraints[added_constraints + i]

                variable_indices = [
                    self.variables.index(variable) for variable in constraint.variables
                ]

                rel_variable_registers = [
                    self.variable_registers[variable_index]
                    for variable_index in variable_indices
                ]

                constraint.build(
                    circuit,
                    variable_registers=rel_variable_registers,
                    ancilla_register=self.ancilla_register,
                    signal_register=self.signal_register,
                    signal_qubit=i
                )

            if self.signal_qubits == 1:
                circuit.p(theta=np.pi / len(self.constraints),
                          qubit=self.signal_register[-1])
            else:
                circuit.mcp(
                    lam=np.pi * self.signal_qubits / len(self.constraints),
                    control_qubits=self.signal_register[:-1],
                    target_qubit=self.signal_register[-1]
                )

            for i in range(self.signal_qubits):
                constraint = self.constraints[added_constraints + i]

                variable_indices = [
                    self.variables.index(variable) for variable in constraint.variables
                ]

                rel_variable_registers = [
                    self.variable_registers[variable_index]
                    for variable_index in variable_indices
                ]

                constraint.build(
                    circuit,
                    variable_registers=rel_variable_registers,
                    ancilla_register=self.ancilla_register,
                    signal_register=self.signal_register,
                    signal_qubit=i
                )

            circuit.barrier()

            added_constraints += self.signal_qubits

        # handle last round separately
        remaining_constraints = len(
            self.constraints) - buffer_rounds * self.signal_qubits

        if remaining_constraints == 0:
            return

        for i in range(remaining_constraints):
            constraint = self.constraints[added_constraints + i]

            variable_indices = [
                self.variables.index(variable) for variable in constraint.variables
            ]

            rel_variable_registers = [
                self.variable_registers[variable_index]
                for variable_index in variable_indices
            ]

            constraint.build(
                circuit,
                variable_registers=rel_variable_registers,
                ancilla_register=self.ancilla_register,
                signal_register=self.signal_register,
                signal_qubit=i
            )

        if remaining_constraints == 1:
            circuit.p(theta=np.pi / len(self.constraints),
                      qubit=self.signal_register[0])
        else:
            circuit.mcp(
                lam=np.pi * remaining_constraints / len(self.constraints),
                control_qubits=self.signal_register[:remaining_constraints - 1],
                target_qubit=self.signal_register[remaining_constraints - 1]
            )

        for i in range(remaining_constraints):
            constraint = self.constraints[added_constraints + i]

            variable_indices = [
                self.variables.index(variable) for variable in constraint.variables
            ]

            rel_variable_registers = [
                self.variable_registers[variable_index]
                for variable_index in variable_indices
            ]

            constraint.build(
                circuit,
                variable_registers=rel_variable_registers,
                ancilla_register=self.ancilla_register,
                signal_register=self.signal_register,
                signal_qubit=i
            )

        circuit.barrier()

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
