from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister, AncillaRegister
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


def init_registers(variables: List[Variable], constraints: List[Constraint]) -> Tuple[List[QuantumRegister], QuantumRegister, QuantumRegister]:
    variable_registers = [
        QuantumRegister(variable.qubit_count, variable.name)
        for variable in variables
    ]

    total_ancilla_qubits = sum(
        [constraint.ancilla_count for constraint in constraints])
    ancilla_register = AncillaRegister(
        total_ancilla_qubits, name="anc")

    total_signal_qubits = len(constraints) + 1
    signal_register = AncillaRegister(
        total_signal_qubits, name="sig")

    return variable_registers, ancilla_register, signal_register


class CircuitBuilder:
    variables: List[Variable]

    def __init__(self, variables: List[Variable]):
        self.variables = variables
        add_allowed_value_constraints(self.variables)

    def initialize_registers(self) -> Tuple[List[QuantumRegister], QuantumRegister, QuantumRegister]:
        constraints = extract_constraints(self.variables)
        variable_registers, ancilla_register, signal_register = init_registers(
            self.variables, constraints
        )
        return variable_registers, ancilla_register, signal_register

    def create_circuit(self, variable_registers: List[QuantumRegister], ancilla_register: QuantumRegister, signal_register: QuantumRegister) -> QuantumCircuit:
        return QuantumCircuit(
            *variable_registers, ancilla_register, signal_register)

    def add_oracle(self, circuit: QuantumCircuit) -> None:
        variable_registers = circuit.qregs[:len(self.variables)]
        ancilla_register = circuit.qregs[len(self.variables)]
        signal_register = circuit.qregs[len(self.variables) + 1]

        # TODO: Sort constraints to minimize depth
        constraints = extract_constraints(self.variables)
        add_constraints_to_circuit(circuit, variable_registers, ancilla_register, signal_register,
                                   self.variables, constraints)

        merge_constraint_results(circuit, signal_register)

        # Uncompute circuit
        add_constraints_to_circuit(circuit, variable_registers, ancilla_register, signal_register,
                                   self.variables, constraints)
