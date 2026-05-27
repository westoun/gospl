
from typing import List


def construct_mcx_gate(control_qubits: List[int], target_qubit: int) -> str:
    gate = "C" * len(control_qubits) + "X("
    for qubit in control_qubits:
        gate += f"{qubit}, "
    gate += f"{target_qubit})"

    return gate


def construct_cx_gate(control_qubit: int, target_qubit: int) -> str:
    return construct_mcx_gate([control_qubit], target_qubit)
