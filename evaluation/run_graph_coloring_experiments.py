import subprocess

seed_num = 30
seed_offset = 0

node_counts = [5]
edge_counts = [8]
color_count = 4
buffer_qubits = [None, 1, 3, 5]
tag = None

for seed_i in range(seed_num):
    seed = seed_offset + seed_i

    for node_count in node_counts:
        for edge_count in edge_counts:

            for buffer_qubit_count in buffer_qubits:

                command = ["python", "graph_coloring.py", "-n",
                           str(node_count), "-e", str(edge_count), "-c", str(color_count), "-s", str(seed)]

                if buffer_qubit_count is not None:
                    command.extend(["-bq", str(buffer_qubit_count)])

                if tag is not None:
                    command.extend(["-t", tag])

                subprocess.run(command)
