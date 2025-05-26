import numpy as np
import itertools
from collections import defaultdict # For grouping bets by type

# Import from project files
try:
    from qubo_formulation import (
        initial_data_load, 
        formulate_qubo_for_budget, 
        LAMBDA_PENALTY,
    )
except ImportError as e:
    print(f"Error importing from qubo_formulation: {e}.")
    def initial_data_load(): return None, [], {} 
    def formulate_qubo_for_budget(b, nf, hd, ct, lp): return None, []
    LAMBDA_PENALTY = 50.0

# Qiskit imports
qiskit_available = False
try:
    from qiskit_aer import AerSimulator 
    from qiskit.algorithms.optimizers import COBYLA
    from qiskit.algorithms.minimum_eigensolvers import QAOA 
    from qiskit.quantum_info import SparsePauliOp
    from qiskit.utils import algorithm_globals
    from qiskit.primitives import Sampler
    qiskit_available = True
except ImportError:
    print("Qiskit not found/version mismatch. Qiskit QAOA skipped.")

# Cirq imports
cirq_available = False
try:
    import cirq
    from scipy.optimize import minimize as scipy_minimize 
    cirq_available = True
except ImportError:
    print("Cirq or Scipy not found. Cirq QAOA skipped.")

# Amazon Braket imports
braket_available = False
try:
    import braket.circuits as bc
    from braket.devices import LocalSimulator
    import braket.observables as bo
    if not 'scipy_minimize' in locals(): 
        from scipy.optimize import minimize as scipy_minimize
    braket_available = True
except ImportError:
    print("Amazon Braket SDK or Scipy not found. Braket QAOA skipped.")


def qubo_to_ising(Q_mat):
    if Q_mat is None: return None, None, 0.0
    num_vars = Q_mat.shape[0]
    h_coeffs = np.zeros(num_vars)
    J_coeffs_dict = {} 
    offset = 0.0
    for i in range(num_vars):
        q_ii = Q_mat[i, i]
        offset += q_ii / 2.0
        h_coeffs[i] -= q_ii / 2.0
    for i in range(num_vars):
        for j in range(i + 1, num_vars):
            q_ij = Q_mat[i, j] 
            if q_ij == 0: continue
            offset += q_ij / 4.0
            h_coeffs[i] -= q_ij / 4.0
            h_coeffs[j] -= q_ij / 4.0
            J_coeffs_dict[(i, j)] = q_ij / 4.0
    return h_coeffs, J_coeffs_dict, offset

# --- Qiskit Functions ---
def execute_qaoa_qiskit(ising_operator, num_qubits, p_layers=1):
    if not qiskit_available: return None
    print(f"\n--- Running Qiskit QAOA (p={p_layers}) ---")
    algorithm_globals.random_seed = 42
    optimizer = COBYLA(maxiter=250)
    try:
        sampler = Sampler()
        qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=p_layers)
    except Exception:
        try:
            from qiskit.utils import QuantumInstance 
            backend = AerSimulator(method='statevector')
            quantum_instance = QuantumInstance(backend, seed_simulator=algorithm_globals.random_seed, seed_transpiler=algorithm_globals.random_seed)
            from qiskit.algorithms import QAOA as OldQAOA
            qaoa = OldQAOA(optimizer=optimizer, reps=p_layers, quantum_instance=quantum_instance)
        except Exception as e_qi:
            print(f"Error setting up Qiskit QAOA (tried Sampler & QuantumInstance): {e_qi}")
            return None
    try:
        result = qaoa.compute_minimum_eigenvalue(operator=ising_operator)
        print("Qiskit QAOA computation complete.")
        return result
    except Exception as e:
        print(f"Error during Qiskit QAOA execution: {e}")
        return None

# --- Cirq Functions ---
def ising_to_cirq_hamiltonian(h_coeffs, J_coeffs_dict, num_qubits):
    if not cirq_available: return None
    qubits = cirq.LineQubit.range(num_qubits)
    hamiltonian = cirq.PauliSum()
    for i in range(num_qubits):
        if not np.isclose(h_coeffs[i], 0): hamiltonian += h_coeffs[i] * cirq.Z(qubits[i])
    for (i, j), coeff in J_coeffs_dict.items():
        if not np.isclose(coeff, 0): hamiltonian += coeff * cirq.Z(qubits[i]) * cirq.Z(qubits[j])
    return hamiltonian

def qaoa_ansatz_cirq(params, qubits, problem_hamiltonian_operator, p_layers):
    circuit = cirq.Circuit(cirq.H(q) for q in qubits)
    gammas = params[:p_layers]; betas = params[p_layers:]
    for k in range(p_layers):
        if problem_hamiltonian_operator: 
            circuit.append(cirq.PauliSumExponential(problem_hamiltonian_operator, exponent=-1j * gammas[k]))
        circuit.append(cirq.Moment(cirq.rx(2 * betas[k])(q) for q in qubits))
    return circuit

def execute_qaoa_cirq(problem_hamiltonian_operator, num_qubits, p_layers=1, ising_offset=0.0):
    if not cirq_available: return None
    print(f"\n--- Running Cirq QAOA (p={p_layers}) ---")
    qubits = cirq.LineQubit.range(num_qubits)
    simulator = cirq.Simulator()
    def qaoa_objective_cirq(params):
        circuit = qaoa_ansatz_cirq(params, qubits, problem_hamiltonian_operator, p_layers)
        exp_val = 0.0
        if problem_hamiltonian_operator: 
            exp_val = simulator.simulate_expectation_values(circuit, observables=problem_hamiltonian_operator).real
        return exp_val + ising_offset
    initial_params = np.random.rand(2 * p_layers) * np.pi
    optimizer_result = scipy_minimize(qaoa_objective_cirq, initial_params, method='COBYLA', options={'maxiter': 200})
    optimal_params, optimal_value = optimizer_result.x, optimizer_result.fun
    print(f"Cirq Scipy optimization complete. Optimal value (energy): {optimal_value:.4f}")
    final_circuit = qaoa_ansatz_cirq(optimal_params, qubits, problem_hamiltonian_operator, p_layers)
    final_statevector = simulator.simulate(final_circuit).final_state_vector
    probabilities = np.abs(final_statevector)**2
    most_likely_int = np.argmax(probabilities)
    most_likely_bitstring = format(most_likely_int, f'0{num_qubits}b') # MSB
    return {'optimal_params': optimal_params, 'optimal_value': optimal_value, 'most_likely_bitstring': most_likely_bitstring}

# --- Amazon Braket Functions ---
def ising_to_braket_hamiltonian(h_coeffs, J_coeffs_dict, num_qubits):
    if not braket_available: return None
    terms = []
    for i in range(num_qubits):
        if not np.isclose(h_coeffs[i], 0): terms.append(bo.Z(i) * h_coeffs[i])
    for (i, j), coeff in J_coeffs_dict.items():
        if not np.isclose(coeff, 0): terms.append((bo.Z(i) @ bo.Z(j)) * coeff)
    return bo.Sum(terms) if terms else bo.Sum([bo.I(0) * 0.0]) 

def qaoa_ansatz_braket(params, num_qubits, h_coeffs, J_coeffs_dict, p_layers):
    circuit = bc.Circuit().h(range(num_qubits))
    gammas = params[:p_layers]; betas = params[p_layers:]
    for k in range(p_layers):
        for i in range(num_qubits):
            if not np.isclose(h_coeffs[i], 0.0): circuit.rz(i, 2 * gammas[k] * h_coeffs[i])
        for (i, j), coeff in J_coeffs_dict.items():
            if not np.isclose(coeff, 0.0):
                circuit.cnot(i, j).rz(j, 2 * gammas[k] * coeff).cnot(i, j)
        for q_idx in range(num_qubits): circuit.rx(q_idx, 2 * betas[k])
    return circuit

def execute_qaoa_braket(h_coeffs, J_coeffs_dict, num_qubits, p_layers=1, ising_offset=0.0):
    if not braket_available: return None
    print(f"\n--- Running Braket QAOA (p={p_layers}) ---")
    problem_observable_braket = ising_to_braket_hamiltonian(h_coeffs, J_coeffs_dict, num_qubits)
    device = LocalSimulator(backend="default")
    def qaoa_objective_braket(params):
        circuit = qaoa_ansatz_braket(params, num_qubits, h_coeffs, J_coeffs_dict, p_layers)
        task = device.run(circuit.expectation(observable=problem_observable_braket), shots=0)
        exp_val = task.result().values[0].real
        return exp_val + ising_offset
    initial_params = np.random.rand(2 * p_layers) * np.pi
    optimizer_result = scipy_minimize(qaoa_objective_braket, initial_params, method='COBYLA', options={'maxiter': 200})
    optimal_params, optimal_value = optimizer_result.x, optimizer_result.fun
    print(f"Braket Scipy optimization complete. Optimal value (energy): {optimal_value:.4f}")
    final_circuit_shots = qaoa_ansatz_braket(optimal_params, num_qubits, h_coeffs, J_coeffs_dict, p_layers)
    counts = device.run(final_circuit_shots, shots=2048).result().measurement_counts
    most_likely_bitstring = max(counts, key=counts.get) if counts else '0'*num_qubits # MSB format
    return {'optimal_params': optimal_params, 'optimal_value': optimal_value, 'most_likely_bitstring': most_likely_bitstring}

def format_and_present_portfolio(framework_name, budget_val, bitstring, candidates_local, num_vars_local, qaoa_energy=None, ising_offset_local=None):
    """
    Formats and prints the recommended portfolio of bets in a user-friendly way.
    """
    # Bitstring interpretation:
    # Qiskit (Sampler int keys to bin_key) & Cirq (argmax on statevector then format) results are MSB.
    # Braket (measurement_counts keys) are MSB.
    # We need x_i to correspond to the i-th candidate.
    # If bitstring is 'b_{N-1}b_{N-2}...b_0', then x_i corresponds to b_i (after reversing the string).
    selected_indices = [i for i, bit_char in enumerate(bitstring[::-1]) if bit_char == '1'] # Reverse for LSB indexing
    
    print(f"\n\n✨ --- Portfolio de Apostas Recomendado ({framework_name}) --- ✨")
    print(f"Para o orçamento de R${budget_val:.2f}:")

    if not selected_indices:
        print("  Nenhuma aposta selecionada pela otimização QAOA.")
        if qaoa_energy is not None:
            actual_ising_offset = ising_offset_local if ising_offset_local is not None else 0.0
            energy_to_print = qaoa_energy if framework_name != "Qiskit" else qaoa_energy + actual_ising_offset
            print(f"  Energia final da otimização: {energy_to_print:.4f}")
        return

    portfolio_summary_parts = defaultdict(int)
    detailed_bet_strings = []
    total_cost = 0.0
    total_score_sum = 0.0 # Sum of scores of selected bets

    for i in selected_indices:
        if i < len(candidates_local):
            bet = candidates_local[i]
            total_cost += bet['cost']
            total_score_sum += bet['score']
            portfolio_summary_parts[bet['type']] += 1
            # Sort combination numbers for consistent display
            combo_str = ", ".join(f"{n:02d}" for n in sorted(bet['combination']))
            detailed_bet_strings.append(f"  Aposta {len(detailed_bet_strings) + 1} ({bet['type']} números): [{combo_str}] (Custo: R${bet['cost']:.2f}, Score: {bet['score']:.4f})")
        else:
            print(f"  Alerta: Índice {i} da solução QAOA está fora dos limites da lista de candidatos.")

    # Construct summary string part for counts
    summary_counts_str_parts = []
    for bet_type, count in sorted(portfolio_summary_parts.items()):
        plural_s = "s" if count > 1 else ""
        num_str = "número" if count == 1 else "números" # For "aposta de X números"
        summary_counts_str_parts.append(f"{count} aposta{plural_s} de {bet_type} {num_str}")
    
    if summary_counts_str_parts:
        summary_str = "Realizar " + " e ".join(summary_counts_str_parts)
        print(f"  {summary_str} (custo total: R${total_cost:.2f}, score total estimado: {total_score_sum:.4f}).")
    else: # Should not happen if selected_indices is not empty
        print("  Nenhuma aposta válida encontrada na seleção.")

    if detailed_bet_strings:
        print("\n  Combinações de Números Detalhadas:")
        for s in detailed_bet_strings:
            print(s)
    
    # Print energy details (optional, for diagnostics)
    if qaoa_energy is not None:
        actual_ising_offset = ising_offset_local if ising_offset_local is not None else 0.0
        energy_to_print = qaoa_energy
        if framework_name == "Qiskit": # Qiskit's eigenvalue does not include offset
            energy_to_print += actual_ising_offset
        print(f"  Energia final da otimização ({framework_name}): {energy_to_print:.4f}")
    elif actual_ising_offset is not None:
         print(f"  Energia efetiva ({framework_name}, apenas offset): {actual_ising_offset:.4f}")
    print("--------------------------------------------------------------------")


def main():
    print("--- Starting QAOA Implementation for Bet Selection (Multiple Budgets) ---")

    print("Loading initial data for QUBO (number frequency, historical draws, cost table)...")
    number_frequency, historical_draws, cost_table_loaded = initial_data_load()

    if number_frequency is None or not cost_table_loaded:
        print("Error: Failed to load necessary data. Exiting QAOA.")
        return

    budgets_to_run = [100.0, 300.0]

    for current_budget in budgets_to_run:
        print(f"\n\n======================================================================")
        print(f"Processing for Budget: R${current_budget:.2f}")
        print(f"======================================================================")

        Q_matrix_current, candidate_bets_current = formulate_qubo_for_budget(
            current_budget, 
            number_frequency, 
            historical_draws, 
            cost_table_loaded,
            LAMBDA_PENALTY 
        )

        if Q_matrix_current is None or not candidate_bets_current:
            print(f"Error: QUBO formulation failed for budget R${current_budget:.2f}. Skipping QAOA for this budget.")
            continue

        num_vars = Q_matrix_current.shape[0]
        if num_vars == 0: 
            print(f"Error: Q_matrix is empty (0 candidates for budget R${current_budget:.2f}). Skipping QAOA.")
            continue
        # print(f"QUBO matrix generated for budget R${current_budget:.2f} with {num_vars} variables.") # Already printed by formulate_qubo

        h_coeffs, J_coeffs_dict, offset = qubo_to_ising(Q_matrix_current)
        if h_coeffs is None: 
            print(f"Failed to convert QUBO to Ising for budget R${current_budget:.2f}. Skipping QAOA."); continue
        
        # print(f"\n--- Ising Parameters (Budget: R${current_budget:.2f}) --- \nOffset: {offset:.4f}\nh_coeffs (first 5): {[f'{c:.2f}' for c in h_coeffs[:min(5,num_vars)]]}\nJ_coeffs (first 5): { {k:f'{v:.2f}' for i,(k,v) in enumerate(J_coeffs_dict.items()) if i<5} }") # Verbose, can be commented

        if num_vars > 22: 
            print(f"Warning: N={num_vars} qubits too large for full statevector simulation. QAOA may be slow/crash or use significant memory.")
        
        qaoa_executed_successfully_for_budget = False
        best_bitstring_for_budget = None
        final_qaoa_energy = None
        framework_used = "N/A"

        if qiskit_available:
            framework_used = "Qiskit"
            print(f"\n--- Attempting Qiskit QAOA for Budget R${current_budget:.2f} ---")
            pauli_list_q = []
            for i in range(num_vars): 
                if not np.isclose(h_coeffs[i], 0):
                    pauli_term = ['I']*num_vars; pauli_term[num_vars-1-i] = 'Z'; pauli_list_q.append(("".join(pauli_term), h_coeffs[i]))
            for (i,j),c in J_coeffs_dict.items():
                if not np.isclose(c,0):
                    pauli_term = ['I']*num_vars; pauli_term[num_vars-1-i] = 'Z'; pauli_term[num_vars-1-j] = 'Z'; pauli_list_q.append(("".join(pauli_term),c))
            q_op = SparsePauliOp.from_list(pauli_list_q) if pauli_list_q else SparsePauliOp(["I"*num_vars],[0])
            
            q_res = execute_qaoa_qiskit(q_op, num_vars)
            if q_res and hasattr(q_res, 'eigenstate') and q_res.eigenstate and hasattr(q_res, 'eigenvalue'):
                qaoa_executed_successfully_for_budget = True
                if isinstance(q_res.eigenstate, dict):
                    processed_probs = { (format(k, f'0{num_vars}b') if isinstance(k,int) else k):v for k,v in q_res.eigenstate.items()}
                    if processed_probs: best_bitstring_for_budget = max(processed_probs, key=processed_probs.get)
                if best_bitstring_for_budget:
                    final_qaoa_energy = q_res.eigenvalue.real # Qiskit eigenvalue does not include offset
                else: print(f"Could not determine best bitstring from Qiskit QAOA for budget R${current_budget:.2f}.")
            else: print(f"Qiskit QAOA failed or no result for budget R${current_budget:.2f}.")

        if not qaoa_executed_successfully_for_budget and cirq_available:
            framework_used = "Cirq"
            print(f"\n--- Attempting Cirq QAOA for Budget R${current_budget:.2f} ---")
            cirq_op = ising_to_cirq_hamiltonian(h_coeffs, J_coeffs_dict, num_vars)
            is_cirq_op_zero = not (cirq_op and any(not np.isclose(term.coefficient.real,0) for term in cirq_op)) # Check if PauliSum has non-zero terms
            
            if is_cirq_op_zero:
                print(f"Cirq Hamiltonian operator part is zero. Energy is offset: {offset:.4f}. Skipping optimization for budget R${current_budget:.2f}.")
                c_res = {'optimal_params':[], 'optimal_value':offset, 'most_likely_bitstring':'0'*num_vars}
            else:
                c_res = execute_qaoa_cirq(cirq_op, num_vars, ising_offset=offset)

            if c_res:
                qaoa_executed_successfully_for_budget = True
                best_bitstring_for_budget = c_res['most_likely_bitstring']
                final_qaoa_energy = c_res['optimal_value'] # Cirq objective includes offset
            else: print(f"Cirq QAOA failed or no result for budget R${current_budget:.2f}.")

        if not qaoa_executed_successfully_for_budget and braket_available:
            framework_used = "Braket"
            print(f"\n--- Attempting Braket QAOA for Budget R${current_budget:.2f} ---")
            b_res = execute_qaoa_braket(h_coeffs, J_coeffs_dict, num_vars, ising_offset=offset)
            if b_res:
                qaoa_executed_successfully_for_budget = True
                best_bitstring_for_budget = b_res['most_likely_bitstring'] # MSB format
                final_qaoa_energy = b_res['optimal_value'] # Braket objective includes offset
            else: print(f"Braket QAOA failed or no result for budget R${current_budget:.2f}.")

        # Present portfolio if successful for this budget
        if qaoa_executed_successfully_for_budget and best_bitstring_for_budget:
            format_and_present_portfolio(framework_used, current_budget, best_bitstring_for_budget, candidate_bets_current, num_vars, final_qaoa_energy, offset if framework_used == "Qiskit" else None)
        elif qaoa_executed_successfully_for_budget and not best_bitstring_for_budget:
             print(f"QAOA with {framework_used} completed for budget R${current_budget:.2f}, but no optimal bitstring was determined.")
        else:
            print(f"\nNo QAOA framework ran successfully for budget R${current_budget:.2f}.")
    
    print("\n--- QAOA Implementation Script Complete ---")

if __name__ == "__main__":
    main()
