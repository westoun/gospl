import subprocess

seed_num = 30
seed_offset = 0

tag = None 

experiment_setups = [
    (2, [1, 3, 5, None]),
    (4, [1, 3, 5, 10, None]),
    (5, [1, 3, 5, 10, None])
]

for seed_i in range(seed_num):
    seed = seed_offset + seed_i

    for variable_count, ancilla_qubits in experiment_setups:
        for ancilla_qubit_count in ancilla_qubits:
            
            command = ["python", "sudoku.py", "-v", str(variable_count), "-s", str(seed)]

            if ancilla_qubit_count is not None:
                command.extend(["-a", str(ancilla_qubit_count)])

            if tag is not None:
                command.extend(["-t", tag])

            subprocess.run(command)
