import math
from typing import List

from .variable import Variable
from .constraint import Constraint
from .utils import construct_mcx_gate


class CircuitBuilder:
    variables: List[Variable]

    def __init__(self, variables: List[Variable]):
        self.variables = variables

    def build(self) -> str:

        constraints: List[Constraint] = []
        for variable in self.variables:

            # Add removal of invalid values constraint
            # for each variable.

            for constraint in variable.constraints:
                if constraint not in constraints:
                    constraints.append(constraint)

        # Sort constraints to reduce depth

        # manage ancillas and build circuit
        total_variable_qubits = 0

        variable_qubit_mapping = {}
        for variable in self.variables:
            qubits_per_variable = math.ceil(math.log2(len(variable.allowed)))
            variable_qubit_mapping[variable] = [
                total_variable_qubits + i for i in range(qubits_per_variable)
            ]
            total_variable_qubits += qubits_per_variable

        total_signal_qubits = len(constraints) + 1

        used_ancillas = 0
        used_signal_qubits = 0

        circuit = ""
        for constraint in constraints:

            variable_qubits: List[List[int]] = []
            for variable in constraint.variables:
                variable_qubits.append(
                    variable_qubit_mapping[variable]
                )

            required_ancillas = constraint.ancilla_count
            ancilla_qubits = [
                total_variable_qubits +
                total_signal_qubits +
                used_ancillas +
                              i for i in range(required_ancillas)]
            
            signal_qubit = total_variable_qubits + used_signal_qubits

            circuit += "\n" + constraint.build(
                variable_qubits, ancilla_qubits, signal_qubit
            )

            used_ancillas += required_ancillas
            used_signal_qubits += 1

        signal_qubits = [
            total_variable_qubits + i for i in range(total_signal_qubits - 1)
        ]
        circuit += "\n" + construct_mcx_gate(
            control_qubits=signal_qubits, target_qubit=total_signal_qubits - 1
        )

        # uncompute circuit

        return circuit
