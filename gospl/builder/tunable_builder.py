import math
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


class TunableBuilder(BuilderBase):
    buffer_qubits: int

    constraints: List[Constraint]

    def __init__(self, variables: List[Variable], buffer_qubits: int = None):
        self.constraints = extract_constraints(variables)

        if buffer_qubits is None:
            print(f"Setting buffer qubits to number of constraints ({len(self.constraints)}).")
            buffer_qubits = len(self.constraints)
            
        elif buffer_qubits < 1:
            print(f"Invalid number of buffer qubits specified ({buffer_qubits}). Setting to number of constraints ({len(self.constraints)}).")
            buffer_qubits = len(self.constraints)

        elif buffer_qubits > len(self.constraints):
            print(f"More buffer qubits provided than constraints ({buffer_qubits} > {len(self.constraints)}). Setting buffer qubits to number of constraints.")
            buffer_qubits = len(self.constraints)

        self.buffer_qubits = buffer_qubits

        super().__init__(variables)

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

    def add_oracle(self, circuit: QuantumCircuit) -> None:
        prepare_kickback_qubit(
            circuit, self.signal_register, self.buffer_qubits)
        add_constraints_to_circuit(circuit, self.variable_registers, self.ancilla_register, self.signal_register,
                                   self.variables, self.constraints, self.buffer_qubits)
