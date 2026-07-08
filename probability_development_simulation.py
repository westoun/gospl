from matplotlib import pyplot as plt
import math 
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import StatevectorSimulator

if __name__ == "__main__":

    qubit_count = 10
    constraint_count = 10
    marked_states_per_constraint = {
        10: 1,
        # 9: 5,
        # # 2: 3
        # 1: 30
    }
    max_n = math.ceil(math.sqrt(2**qubit_count))

    circuit = QuantumCircuit(qubit_count)

    def apply_oracle():

        state_i = 0

        for satisfaction_count in sorted(marked_states_per_constraint, reverse=True):

            for _ in range(marked_states_per_constraint[satisfaction_count]):

                bit_string = bin(state_i)[2:].zfill(qubit_count)

                # map state to |1...1>
                for bit_i, bit_value in enumerate(bit_string):

                    if bit_value == "0":
                        circuit.x(bit_i)

                # apply cphase
                circuit.mcp(
                    lam=np.pi / constraint_count * satisfaction_count,
                    control_qubits=list(range(qubit_count - 1)),
                    target_qubit=list(range(qubit_count))[-1]
                )

                # map state back
                for bit_i, bit_value in enumerate(bit_string):

                    if bit_value == "0":
                        circuit.x(bit_i)

                state_i += 1

        circuit.barrier()

    def apply_diffusor():
        for i in range(qubit_count):
            circuit.h(i)
            circuit.x(i)

        circuit.h(qubit_count - 1)
        circuit.mcx(list(range(qubit_count - 1)), qubit_count - 1)
        circuit.h(qubit_count - 1)

        for i in range(qubit_count):
            circuit.x(i)
            circuit.h(i)

        circuit.barrier()

    # RUN CIRCUIT
    
    for i in range(qubit_count):
        circuit.h(i)

    circuit.barrier()

    for i in range(max_n):
        apply_oracle()
        apply_diffusor()

        circuit.save_statevector(f"state_{i}")

    simulator = StatevectorSimulator()
    result = simulator.run(transpile(circuit, simulator)).result()
    data = result.data()

    # EXTRACT PROBABILITIES AFTER EACH ITERATION
    probabilities_per_label = {}
    for satisfaction_count in sorted(marked_states_per_constraint, reverse=True):
        probabilities_per_label[satisfaction_count] = []

    for i in range(max_n):

        state_vector = data[f"state_{i}"]

        # Reversing the order of qubits is needed to align with original
        # top-down encoding
        probabilities = state_vector.probabilities(
            qargs=list(reversed(list(range(qubit_count)))))

        state_i = 0
        for satisfaction_count in sorted(marked_states_per_constraint, reverse=True):

            probabilities_per_satisfaction_count = []

            for _ in range(marked_states_per_constraint[satisfaction_count]):

                probabilities_per_satisfaction_count.append(
                    float(probabilities[state_i]))
                state_i += 1

            probabilities_per_label[satisfaction_count].append(
                probabilities_per_satisfaction_count[0])

    correlations = []
    for i in range(max_n):
        
        satisfaction_counts = []
        probabilities = []

        for satisfaction_count in probabilities_per_label:
            satisfaction_counts.append(satisfaction_count)
            probabilities.append(probabilities_per_label[satisfaction_count][i])

        correlation = np.corrcoef(satisfaction_counts, probabilities)[0, 1]
        correlations.append(correlation)


    # VISUALIZE RESULTS
    ax = plt.subplot()
    for satisfaction_count in probabilities_per_label:
        ax.plot(range(max_n), probabilities_per_label[satisfaction_count],
                label=f"{satisfaction_count} / {constraint_count} constraints")

    ax.plot(range(max_n), correlations, label="correlation between sat. and prob.", color="grey", linestyle="dashed")

    ax.set_ylim((0, 1))

    ax.set_xlabel("iteration")

    ax.set_ylabel("probability")

    plt.grid()
    plt.legend()

    plt.show()
    plt.clf()
