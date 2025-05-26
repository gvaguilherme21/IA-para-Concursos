import pandas as pd
import numpy as np
import itertools
import random
from collections import Counter

# Attempt to import from project files
try:
    from data_processor import df_lotofacil, COST_TABLE, load_data
    from scoring_model import calculate_score, get_15_number_sub_combinations, score_candidate_bet
except ImportError as e:
    print(f"Error importing project modules: {e}. Ensure all project files are accessible.")
    if 'df_lotofacil' not in locals(): 
        df_lotofacil = pd.DataFrame({'numeros_list': []}) 
    if 'COST_TABLE' not in locals():
        COST_TABLE = {15: {"cost": 3.00}, 16: {"cost": 48.00}, 17: {"cost": 408.00}, 18: {"cost": 2448.00}}
    # Dummy scoring functions if not imported
    if 'calculate_score' not in locals():
        def calculate_score(combo, freq): return (random.random() * 2 + 2, {}) # Returns score ~2-4
    if 'score_candidate_bet' not in locals():
        def score_candidate_bet(combo, freq): return random.random() * 2 + 2


# Global constant for penalty
LAMBDA_PENALTY = 50.0

# Global placeholders for import by other modules (populated by the direct run of this script)
Q_matrix_generated = None
candidate_bets_list_generated = None
active_df_for_import = None # To hold the loaded df for qaoa_implementation if needed

def calculate_number_frequency_internal(df): # Renamed to avoid conflict if imported
    all_numbers = []
    if df is not None and not df.empty and 'numeros_list' in df.columns:
        for numbers in df['numeros_list']:
            if isinstance(numbers, list):
                all_numbers.extend(numbers)
    return Counter(all_numbers)

def formulate_qubo_for_budget(budget, number_frequency, historical_draws, cost_table_local, lambda_penalty_local):
    """
    Selects candidate bets and formulates the QUBO matrix for a given budget.
    """
    print(f"\n--- Starting QUBO Formulation for Budget: R${budget:.2f} ---")
    
    candidate_bets_list = []
    
    # 1.1. 15-Number Bets (Top 50 historical)
    print("--- Selecting 15-Number Candidate Bets ---")
    scored_15_number_historical = []
    for combo in historical_draws: # historical_draws is already df['numeros_list']
        if isinstance(combo, list) and len(combo) == 15: # Ensure it's a valid list
            score, _ = calculate_score(combo, number_frequency)
            cost = cost_table_local.get(15, {}).get("cost", 3.00) 
            scored_15_number_historical.append({'combination': combo, 'score': score, 'cost': cost, 'type': 15})
    
    scored_15_number_historical.sort(key=lambda x: x['score'], reverse=True)
    top_50_15_number_bets = scored_15_number_historical[:50]
    candidate_bets_list.extend(top_50_15_number_bets)
    print(f"Selected {len(top_50_15_number_bets)} top 15-number historical bets.")
    if top_50_15_number_bets:
        print(f"Example top 15-number bet: Score={top_50_15_number_bets[0]['score']:.4f}")

    # 1.2. 16-Number Bets (Generated, 50 candidates)
    print("\n--- Selecting 16-Number Candidate Bets ---")
    NUM_16_NUMBER_CANDIDATES_TO_GENERATE = 50
    TOP_N_FREQUENT_NUMBERS = 20
    most_common_numbers_tuples = number_frequency.most_common(TOP_N_FREQUENT_NUMBERS)
    frequent_numbers_pool = [num for num, freq in most_common_numbers_tuples]
    generated_16_number_bets = []

    if len(frequent_numbers_pool) < 16:
        print(f"Warning: Not enough frequent numbers (found {len(frequent_numbers_pool)}) to generate 16-number combinations.")
    else:
        generated_16_combos_set = set()
        attempts = 0
        max_attempts = NUM_16_NUMBER_CANDIDATES_TO_GENERATE * 10
        while len(generated_16_number_bets) < NUM_16_NUMBER_CANDIDATES_TO_GENERATE and attempts < max_attempts:
            attempts += 1
            current_sample_size = min(16, len(frequent_numbers_pool))
            if current_sample_size < 16: break
            candidate_16_list = sorted(random.sample(frequent_numbers_pool, 16))
            candidate_16_tuple = tuple(candidate_16_list)
            if candidate_16_tuple not in generated_16_combos_set:
                generated_16_combos_set.add(candidate_16_tuple)
                bet_score = score_candidate_bet(candidate_16_list, number_frequency)
                cost = cost_table_local.get(16, {}).get("cost", 48.00)
                generated_16_number_bets.append({'combination': candidate_16_list, 'score': bet_score, 'cost': cost, 'type': 16})
    
    candidate_bets_list.extend(generated_16_number_bets)
    print(f"Generated and selected {len(generated_16_number_bets)} 16-number bets.")
    if generated_16_number_bets:
        generated_16_number_bets.sort(key=lambda x: x['score'], reverse=True)
        if generated_16_number_bets:
             print(f"Example generated 16-number bet: Score={generated_16_number_bets[0]['score']:.4f}")
    
    # Future: Add 17/18 number candidates if budget allows (e.g. for R$300 budget)
    if budget >= cost_table_local.get(17,{}).get("cost", 408.00) : # Example cost for 17 numbers
        # Add logic for 17-number bets (e.g., 20 candidates)
        pass # Placeholder
    if budget >= cost_table_local.get(18,{}).get("cost", 2448.00): # Example cost for 18 numbers
        # Add logic for 18-number bets (e.g., 10 candidates)
        pass # Placeholder


    if not candidate_bets_list:
        print("Error: No candidate bets selected or generated for this budget. Cannot formulate QUBO.")
        return None, []

    # 2. Construct QUBO Matrix Q
    N = len(candidate_bets_list)
    Q = np.zeros((N, N))
    print(f"\n--- Constructing QUBO Matrix ({N}x{N}) for Budget R${budget:.2f} ---")
    print(f"Lambda Penalty: {lambda_penalty_local}")

    for i in range(N):
        score_i = candidate_bets_list[i]['score']
        cost_i = candidate_bets_list[i]['cost']
        Q[i, i] += -score_i 
        Q[i, i] += lambda_penalty_local * (cost_i**2 - 2 * budget * cost_i)
    for i in range(N):
        for j in range(i + 1, N):
            cost_i = candidate_bets_list[i]['cost']
            cost_j = candidate_bets_list[j]['cost']
            Q[i, j] += lambda_penalty_local * 2 * cost_i * cost_j
    
    print(f"QUBO formulation complete for budget R${budget:.2f}.")
    return Q, candidate_bets_list


def initial_data_load():
    """Loads data using data_processor.load_data() and calculates frequency."""
    global active_df_for_import # Make df available for qaoa_implementation
    
    # Try to use df_lotofacil populated at import time by data_processor.py
    current_df = df_lotofacil 
    if current_df is None or current_df.empty:
        print("Initial df_lotofacil (from data_processor import) is empty. Attempting explicit load_data()...")
        current_df = load_data() 
    
    active_df_for_import = current_df # Store for potential import by other modules

    if current_df is None or current_df.empty:
        print("Error: Data loading failed or returned empty DataFrame. Cannot proceed.")
        return None, None, []

    print(f"Number of historical draws loaded for frequency calculation: {len(current_df)}")
    number_frequency = calculate_number_frequency_internal(current_df)
    
    historical_draws_for_candidates = []
    if 'numeros_list' in current_df.columns:
        historical_draws_for_candidates = [combo for combo in current_df['numeros_list'] if isinstance(combo, list) and len(combo) == 15]
    
    if not number_frequency:
        print("Error: Number frequency is empty. Cannot effectively score or generate candidates.")
        return None, None, []
        
    print(f"Number Frequency (Top 5 for use in QUBO): {number_frequency.most_common(5)}")
    return number_frequency, historical_draws_for_candidates, COST_TABLE # Return COST_TABLE too

# This function is called if the script is run directly.
# It also populates global Q_matrix_generated and candidate_bets_list_generated for import.
def run_default_qubo_formulation_and_print():
    global Q_matrix_generated, candidate_bets_list_generated
    
    print("--- Running Default QUBO Formulation Setup ---")
    number_frequency, historical_draws, cost_table_local = initial_data_load()

    if number_frequency is None or not historical_draws:
        print("Failed to load data or prepare inputs for QUBO. Aborting default run.")
        return

    test_budget = 100.0 
    Q_matrix_generated, candidate_bets_list_generated = formulate_qubo_for_budget(
        test_budget, 
        number_frequency, 
        historical_draws, 
        cost_table_local, 
        LAMBDA_PENALTY
    )

    if Q_matrix_generated is not None and candidate_bets_list_generated:
        N = len(candidate_bets_list_generated)
        print(f"\n--- Results for Default Budget R${test_budget:.2f} ---")
        print(f"Total number of candidate bets (N): {N}")
        print(f"Lambda Penalty: {LAMBDA_PENALTY}")
        print("\nQUBO Matrix Q (first 5x5 elements):")
        print(Q_matrix_generated[:5, :5])
        print("\nDiagonal elements of Q (Q[i,i] - first N):") # N might be less than 100 if generation fails
        print(np.diag(Q_matrix_generated)[:min(N, len(np.diag(Q_matrix_generated)))])
    else:
        print(f"QUBO formulation failed for default budget R${test_budget:.2f}.")
    print("--- Default QUBO Formulation Setup Complete ---")


if __name__ == "__main__":
    run_default_qubo_formulation_and_print()
    # Q_matrix_generated and candidate_bets_list_generated are now populated
    # for qaoa_implementation.py if it imports this module after this script runs.
    # However, qaoa_implementation.py will call formulate_qubo_for_budget directly.
    # This __main__ block primarily serves for direct testing of qubo_formulation.py.
    # The global variables are for a fallback import scenario, but direct call is cleaner.

# Make key functions and data available for import
# calculate_number_frequency is already global
# formulate_qubo_for_budget is global
# COST_TABLE is imported and thus available if data_processor was found
# LAMBDA_PENALTY is global
# For df_lotofacil and number_frequency for qaoa_implementation:
# qaoa_implementation.py should call initial_data_load() then formulate_qubo_for_budget().
