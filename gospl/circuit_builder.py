import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister, ClassicalRegister
from typing import List, Dict, Tuple

from gospl.variable import Variable
from gospl.constraint import Constraint, LessThan
from .utils import extract_constraints


def add_constraints_to_circuit(
    circuit: QuantumCircuit,
    variable_registers: List[QuantumRegister],
    ancilla_register: QuantumRegister,
    signal_register: QuantumRegister,
    variables: List[Variable],
    constraints: List[Constraint],
    buffer_qubits: int
) -> None:

    added_constraints = 0

    buffer_rounds = math.floor(len(constraints) / buffer_qubits)
    for _ in range(buffer_rounds):

        for i in range(buffer_qubits):
            constraint = constraints[added_constraints + i]

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
                signal_register=signal_register,
                signal_qubit=i
            )

        circuit.mcp(
            lam=np.pi / math.ceil(len(constraints) / buffer_qubits),
            control_qubits=signal_register[:-1],
            target_qubit=signal_register[-1]
        )

        for i in range(buffer_qubits):
            constraint = constraints[added_constraints + i]

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
                signal_register=signal_register,
                signal_qubit=i
            )

        circuit.barrier()

        added_constraints += buffer_qubits

    # handle last round separately
    remaining_constraints = len(constraints) - buffer_rounds * buffer_qubits

    if remaining_constraints == 0:
        return

    for i in range(remaining_constraints):
        constraint = constraints[added_constraints + i]

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
            signal_register=signal_register,
            signal_qubit=i
        )

    circuit.mcp(
        lam=np.pi / math.ceil(len(constraints) / buffer_qubits),
        control_qubits=signal_register[:remaining_constraints],
        target_qubit=signal_register[-1]
    )

    for i in range(remaining_constraints):
        constraint = constraints[added_constraints + i]

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
            signal_register=signal_register,
            signal_qubit=i
        )

    circuit.barrier()


def prepare_kickback_qubit(circuit: QuantumCircuit,
                           signal_register: QuantumRegister, buffer_qubits: int) -> None:
    circuit.x(signal_register[buffer_qubits])


def add_allowed_value_constraints(variables: List[Variable]) -> None:
    for variable in variables:
        if 2 ** variable.qubit_count > len(variable.allowed):
            LessThan(variable, len(variable.allowed))


class CircuitBuilder:
    variables: List[Variable]
    constraints: List[Constraint]

    variable_registers: List[QuantumRegister]
    ancilla_register: QuantumRegister
    signal_register: QuantumRegister
    classical_registers: List[ClassicalRegister]

    buffer_qubits: int

    def __init__(self, variables: List[Variable], buffer_qubits: int = None):
        self.variables = variables

        add_allowed_value_constraints(self.variables)

        self.constraints = extract_constraints(variables)

        if buffer_qubits is None:
            print(
                f"Setting buffer qubits to number of constraints ({len(self.constraints)}).")
            buffer_qubits = len(self.constraints)

        elif buffer_qubits < 1:
            print(
                f"Invalid number of buffer qubits specified ({buffer_qubits}). Setting to number of constraints ({len(self.constraints)}).")
            buffer_qubits = len(self.constraints)

        elif buffer_qubits > len(self.constraints):
            print(
                f"More buffer qubits provided than constraints ({buffer_qubits} > {len(self.constraints)}). Setting buffer qubits to number of constraints.")
            buffer_qubits = len(self.constraints)

        self.buffer_qubits = buffer_qubits

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
            self.buffer_qubits + 1, name="sig")

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
        prepare_kickback_qubit(
            circuit, self.signal_register, self.buffer_qubits)
        add_constraints_to_circuit(circuit, self.variable_registers, self.ancilla_register, self.signal_register,
                                   self.variables, self.constraints, self.buffer_qubits)

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
