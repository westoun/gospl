import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import StatevectorSimulator

if __name__ == "__main__":

    qubit_count = 3
    constraint_count = 5
    marked_states_per_constraint = {
        5: 2,
        4: 1
        # 2: 3
    }
    max_n = 3

    circuit = QuantumCircuit(qubit_count + 2)

    def apply_oracle():

        state_i = 0

        for satisfaction_count in sorted(marked_states_per_constraint, reverse=True):

            for _ in range(marked_states_per_constraint[satisfaction_count]):

                bit_string = bin(state_i)[2:].zfill(qubit_count)

                # map state to |1...1>
                for bit_i, bit_value in enumerate(bit_string):

                    if bit_value == "0":
                        circuit.x(bit_i)

                # apply mcx
                circuit.mcx(control_qubits=list(range(qubit_count)),
                            target_qubit=qubit_count)

                # apply cphase
                circuit.cp(
                    theta=np.pi / constraint_count * satisfaction_count,
                    control_qubit=qubit_count,
                    target_qubit=qubit_count + 1
                )

                # apply mcx
                circuit.mcx(control_qubits=list(range(qubit_count)),
                            target_qubit=qubit_count)

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

    # apply hadamard to each qubit
    for i in range(qubit_count):
        circuit.h(i)

    circuit.barrier()

    # mark second ancilla for phase kickback
    circuit.x(qubit_count + 1)

    for i in range(max_n):
        apply_oracle()
        apply_diffusor()

        circuit.save_statevector(f"state_{i}")

    # print(circuit)

    simulator = StatevectorSimulator()
    result = simulator.run(transpile(circuit, simulator)).result()
    data = result.data()

    for i in range(max_n):
        state_vector = data[f"state_{i}"]

        # Reversing the order of qubits is needed to align with original 
        # top-down encoding
        probabilities = state_vector.probabilities(qargs=list(reversed(list(range(qubit_count)))))

        # for state_i, probability in enumerate(probabilities):

        #     state_i = int(state_i)

        #     print(f"{state_i}: {probabilities[state_i]}")

        state_i = 0
        for satisfaction_count in sorted(marked_states_per_constraint, reverse=True):

            probabilities_per_satisfaction_count = []

            for _ in range(marked_states_per_constraint[satisfaction_count]):

                probabilities_per_satisfaction_count.append(float(probabilities[state_i]))
                state_i += 1

            print(f"Probabilities of states that satisfy {satisfaction_count} of {constraint_count} constraints: {probabilities_per_satisfaction_count}")

        # get probabilities of all 


        

        # print(probabilities)

        # get probability distribution

        # get results for each of the marked states

        # add to data collection

    # plot results

    pass
