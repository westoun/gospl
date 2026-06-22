from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister, ClassicalRegister
from typing import List, Dict, Tuple

from .variable import Variable
from .constraint import Constraint, LessThan


def extract_constraints(variables: List[Variable]) -> List[Constraint]:
    constraints: List[Constraint] = []
    for variable in variables:
        for constraint in variable.constraints:
            if constraint not in constraints:
                constraints.append(constraint)

    return constraints


def add_allowed_value_constraints(variables: List[Variable]) -> None:
    for variable in variables:
        if 2 ** variable.qubit_count > len(variable.allowed):
            LessThan(variable, len(variable.allowed))


def add_constraints_to_circuit(
    circuit: QuantumCircuit,
    variable_registers: List[QuantumRegister],
    ancilla_register: QuantumRegister,
    signal_register: QuantumRegister,
    variables: List[Variable], constraints: List[Constraint]
) -> None:
    used_ancillas = 0
    used_signal_qubits = 0
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
            used_signal_qubits=used_signal_qubits
        )
        circuit.barrier()

        used_ancillas += constraint.ancilla_count
        used_signal_qubits += 1


def merge_constraint_results(circuit: QuantumCircuit, signal_register: QuantumRegister) -> None:
    circuit.x(signal_register[-1])
    circuit.h(signal_register[-1])
    circuit.mcx(
        control_qubits=signal_register[:-1], target_qubit=signal_register[-1])

    circuit.barrier()


class CircuitBuilder:
    variables: List[Variable]
    variable_registers: List[QuantumRegister]
    ancilla_register: QuantumRegister
    signal_register: QuantumRegister
    classical_registers: List[ClassicalRegister]

    def __init__(self, variables: List[Variable]):
        self.variables = variables
        add_allowed_value_constraints(self.variables)

    def create_circuit(self) -> QuantumCircuit:
        constraints = extract_constraints(self.variables)

        self.variable_registers = [
            QuantumRegister(variable.qubit_count, variable.name)
            for variable in self.variables
        ]

        total_ancilla_qubits = max(
            [constraint.ancilla_count for constraint in constraints])
        self.ancilla_register = AncillaRegister(
            total_ancilla_qubits, name="anc")

        total_signal_qubits = len(constraints) + 1
        self.signal_register = AncillaRegister(
            total_signal_qubits, name="sig")

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
        # TODO: Sort constraints to minimize depth
        constraints = extract_constraints(self.variables)
        add_constraints_to_circuit(circuit, self.variable_registers, self.ancilla_register, self.signal_register,
                                   self.variables, constraints)

        merge_constraint_results(circuit, self.signal_register)

        # Uncompute circuit
        add_constraints_to_circuit(circuit, self.variable_registers, self.ancilla_register, self.signal_register,
                                   self.variables, constraints)

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
