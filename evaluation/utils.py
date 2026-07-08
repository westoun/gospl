from datetime import datetime
import json
from qiskit import QuantumCircuit
from typing import Tuple, Any


def count_gates(circuit: QuantumCircuit) -> int:
    gate_count = 0
    for gate, count in circuit.count_ops().items():
        gate_count += count
    return gate_count


def save_to_json(obj, path: str) -> None:
    with open(path, "w") as config_file:
        json.dump(obj, config_file)


def load_from_json(path: str) -> Any:
    with open(path, "r") as config_file:
        return json.load(config_file)


def get_timestamp() -> str:
    return str(datetime.now())
