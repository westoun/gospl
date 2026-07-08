import subprocess

seed_num = 30
seed_offset = 0

node_counts = [5]
edge_counts = [8]
color_count = 4
ancilla_qubits = [None, 1, 3, 5]
tag = None

experiment_setups = [
    (4, 3, 3, [1, 3, 5, None]),
    (4, 5, 3, [1, 3, 5, None]),
    (5, 8, 4, [1, 3, 5, None]),
]

for seed_i in range(seed_num):
    seed = seed_offset + seed_i

    for node_count, edge_count, color_count, ancilla_qubits in experiment_setups:

        for ancilla_qubit_count in ancilla_qubits:

            command = ["python", "graph_coloring.py", "-n",
                        str(node_count), "-e", str(edge_count), "-c", str(color_count), "-s", str(seed)]

            if ancilla_qubit_count is not None:
                command.extend(["-a", str(ancilla_qubit_count)])

            if tag is not None:
                command.extend(["-t", tag])

            subprocess.run(command)
