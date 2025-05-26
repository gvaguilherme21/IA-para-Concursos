import pandas as pd
from data_processor import df_lotofacil, COST_TABLE # Assuming df_lotofacil is loaded
from collections import Counter
import itertools
import random

# --- 1. Process 'numeros' column ---
# 'numeros_list' is now expected to be pre-processed in df_lotofacil from data_processor.py
# So, we directly use it. We should still handle cases where it might be missing or empty for robustness.

if df_lotofacil is None or df_lotofacil.empty or 'numeros_list' not in df_lotofacil.columns:
    print("Error: df_lotofacil is not loaded, is empty, or 'numeros_list' is missing.")
    # Initialize df_lotofacil with an empty 'numeros_list' if it's None, to prevent downstream errors.
    if df_lotofacil is None:
        df_lotofacil = pd.DataFrame({'numeros_list': pd.Series([], dtype='object')})
    elif 'numeros_list' not in df_lotofacil.columns:
        df_lotofacil['numeros_list'] = pd.Series([[] for _ in range(len(df_lotofacil))], dtype='object')


# --- 2. Calculate Individual Number Frequency ---
all_numbers = []
# Ensure 'numeros_list' exists and is a Series/iterable
if 'numeros_list' in df_lotofacil.columns and hasattr(df_lotofacil['numeros_list'], '__iter__'):
    for numbers in df_lotofacil['numeros_list']:
        if isinstance(numbers, list): # Ensure it's a list before extending
            all_numbers.extend(numbers)
        # It's possible that even after processing, some lists might be empty if all numbers were invalid
        # or if a row had no valid Bola data. This is acceptable.

number_frequency = Counter(all_numbers)
# print("Number Frequency:", number_frequency)

# --- 3. Define Helper Functions for Scoring Features ---
PRIMES_UP_TO_25 = [2, 3, 5, 7, 11, 13, 17, 19, 23]

def count_even_numbers(combination):
    """Returns the count of even numbers in a given combination."""
    if not isinstance(combination, list): return 0
    return sum(1 for num in combination if num % 2 == 0)

def sum_of_numbers(combination):
    """Returns the sum of numbers in a given combination."""
    if not isinstance(combination, list): return 0
    return sum(combination)

def count_prime_numbers(combination):
    """Returns the count of prime numbers in a given combination."""
    if not isinstance(combination, list): return 0
    return sum(1 for num in combination if num in PRIMES_UP_TO_25)

# --- 4. Define the Main Scoring Function ---
def calculate_score(combination, num_freq):
    """
    Calculates a score for a given 15-number combination based on various features.
    """
    if not isinstance(combination, list) or len(combination) != 15:
        return 0, {"error": "Invalid combination: must be a list of 15 numbers."}

    # --- Feature Calculations ---
    # 1. Frequency Score
    freq_score = sum(num_freq.get(num, 0) for num in combination)

    # 2. Even/Odd Score
    evens = count_even_numbers(combination)
    odds = 15 - evens
    # Heuristic: Ideal is 7 or 8 evens (i.e., 7 evens / 8 odds or 8 evens / 7 odds)
    if evens == 7 or evens == 8:
        even_odd_score = 1.0
    elif evens == 6 or evens == 9:
        even_odd_score = 0.7
    elif evens == 5 or evens == 10:
        even_odd_score = 0.4
    else:
        even_odd_score = 0.1 # Lower score for more unbalanced combinations

    # 3. Sum Score
    current_sum = sum_of_numbers(combination)
    # Heuristic: Ideal sum range (example: 170-220). This is a wide guess.
    # A more data-driven approach would be to use mean and std dev of historical sums.
    # For now, a simple tiered approach:
    if 180 <= current_sum <= 210: # Most ideal
        sum_score = 1.0
    elif 170 <= current_sum < 180 or 210 < current_sum <= 220:
        sum_score = 0.7
    elif 160 <= current_sum < 170 or 220 < current_sum <= 230:
        sum_score = 0.4
    else:
        sum_score = 0.1 # Further from typical sums

    # 4. Prime Score
    primes_count = count_prime_numbers(combination)
    # Heuristic: Ideal is 5 or 6 primes
    if primes_count == 5 or primes_count == 6:
        prime_score = 1.0
    elif primes_count == 4 or primes_count == 7:
        prime_score = 0.7
    elif primes_count == 3 or primes_count == 8:
        prime_score = 0.4
    else:
        prime_score = 0.1

    # --- Normalization (Placeholder/Basic) ---
    # Max possible freq_score: if all 15 numbers in combination are the most frequent number.
    # This is a simplification. A better way would be to sum the top 15 frequencies.
    # For now, let's assume max frequency for a single number is around (total_draws / 25) * 15
    # This is a very rough estimate.
    if not num_freq: # Handle empty num_freq
        freq_score_normalized = 0
    else:
        # A slightly better max_freq_score: sum of frequencies of the 15 most common numbers
        # For simplicity now, let's estimate based on average frequency.
        # Total numbers drawn = len(all_numbers)
        # Total unique numbers = 25
        # Avg freq per number = len(all_numbers) / 25 if all_numbers else 0
        # Max possible for a combination of 15 = avg_freq_per_number * 15
        # This normalization is still very basic and needs refinement.
        # If number_frequency is not empty, use its values.
        max_possible_ind_freq = max(num_freq.values()) if num_freq else 1
        # A rough upper bound for freq_score
        # A more robust approach would be to sum the frequencies of the top 15 most frequent numbers
        # from the historical data. For now, let's use a simpler heuristic.
        # If number_frequency has at least 15 numbers:
        if len(num_freq) >= 15:
             max_freq_score_estimate = sum(sorted(num_freq.values(), reverse=True)[:15])
        elif num_freq: # if less than 15 numbers but some data
            max_freq_score_estimate = sum(num_freq.values()) * (15 / len(num_freq)) # scale up
        else: # no frequency data
            max_freq_score_estimate = 1 # Avoid division by zero

        freq_score_normalized = freq_score / max_freq_score_estimate if max_freq_score_estimate > 0 else 0


    # The other scores are already in a 0-1 range due to heuristics
    even_odd_score_normalized = even_odd_score
    sum_score_normalized = sum_score
    prime_score_normalized = prime_score

    # --- Weighted Sum ---
    w1, w2, w3, w4 = 1.0, 1.0, 1.0, 1.0 # Equal weights for now
    total_score = (w1 * freq_score_normalized) + \
                  (w2 * even_odd_score_normalized) + \
                  (w3 * sum_score_normalized) + \
                  (w4 * prime_score_normalized)

    # Store intermediate scores for analysis
    intermediate_scores = {
        "freq_score_raw": freq_score,
        "freq_score_normalized": freq_score_normalized,
        "even_odd_score": even_odd_score_normalized,
        "sum_score": sum_score_normalized,
        "prime_score": prime_score_normalized,
        "evens_count": evens,
        "sum_value": current_sum,
        "primes_count": primes_count
    }
    return total_score, intermediate_scores

# --- Helper function to get sub-combinations ---
def get_15_number_sub_combinations(original_combination):
    """
    Generates all unique 15-number sub-combinations from an original combination.
    """
    if not isinstance(original_combination, list) or len(original_combination) < 15:
        return []
    return list(itertools.combinations(original_combination, 15))

# --- Function to score a candidate N-number bet ---
def score_candidate_bet(candidate_combination, num_freq):
    """
    Scores a candidate N-number bet by averaging the scores of its 15-number sub-combinations.
    If the candidate is already 15 numbers, it's scored directly.
    """
    if not isinstance(candidate_combination, list):
        # print(f"Warning: Invalid candidate_combination type: {type(candidate_combination)}. Returning score 0.")
        return 0

    num_elements = len(candidate_combination)

    if num_elements < 15:
        # print(f"Warning: Candidate combination {candidate_combination} has less than 15 numbers. Returning score 0.")
        return 0
    
    if num_elements == 15:
        score, _ = calculate_score(candidate_combination, num_freq)
        return score

    # For combinations with more than 15 numbers
    sub_combinations = get_15_number_sub_combinations(candidate_combination)
    if not sub_combinations:
        # This case should ideally not be hit if num_elements > 15, but as a safeguard:
        # print(f"Warning: No 15-number sub-combinations generated for {candidate_combination}. Returning score 0.")
        return 0

    total_score = 0
    valid_sub_scores_count = 0
    for sub_combo_tuple in sub_combinations:
        sub_combo_list = list(sub_combo_tuple) # calculate_score expects a list
        score, details = calculate_score(sub_combo_list, num_freq)
        if "error" not in details: # Ensure the sub-combination was valid for scoring
            total_score += score
            valid_sub_scores_count += 1
    
    if valid_sub_scores_count == 0:
        # print(f"Warning: None of the sub-combinations for {candidate_combination} could be scored. Returning score 0.")
        return 0
        
    return total_score / valid_sub_scores_count


# --- 5. Generate, Score, and Print Candidate Bets ---
if __name__ == "__main__":
    print(f"Number of historical draws loaded: {len(df_lotofacil) if df_lotofacil is not None and not df_lotofacil.empty else 0}")
    
    if df_lotofacil is None or df_lotofacil.empty or 'numeros_list' not in df_lotofacil.columns:
        print("DataFrame 'df_lotofacil' is empty or 'numeros_list' is missing. Cannot generate or score candidates.")
    elif not number_frequency:
        print("Number frequency data is empty. Cannot generate 16-number candidates or score effectively.")
    else:
        print(f"Number Frequency (Top 5): {number_frequency.most_common(5)}")

        # --- 15-Number Candidates (from historical data) ---
        scored_15_number_candidates = []
        if 'numeros_list' in df_lotofacil.columns:
            for combo_15 in df_lotofacil['numeros_list']:
                if isinstance(combo_15, list) and len(combo_15) == 15: # Should always be true due to data_processor
                    score, _ = calculate_score(combo_15, number_frequency)
                    scored_15_number_candidates.append((score, combo_15))
        
        print(f"\n--- 15-Number Candidates (Historical Draws) ---")
        print(f"Total 15-number candidates found: {len(scored_15_number_candidates)}")
        if scored_15_number_candidates:
            scored_15_number_candidates.sort(key=lambda x: x[0], reverse=True)
            print("Top 5 scored 15-number candidates:")
            for i, (score, combo) in enumerate(scored_15_number_candidates[:5]):
                print(f"  {i+1}. Score: {score:.4f}, Combination: {sorted(combo)}")
        else:
            print("No 15-number candidates were scored (e.g., df_lotofacil might be empty or 'numeros_list' problematic).")

        # --- 16-Number Candidate Generation (Heuristic) ---
        NUM_16_NUMBER_CANDIDATES_TO_GENERATE = 100 # As per subtask suggestion (50-100)
        TOP_N_FREQUENT_NUMBERS = 20

        scored_16_number_candidates = []
        
        # Get top N frequent numbers
        most_common_numbers_tuples = number_frequency.most_common(TOP_N_FREQUENT_NUMBERS)
        frequent_numbers_pool = [num for num, freq in most_common_numbers_tuples]

        if len(frequent_numbers_pool) < 16:
            print(f"\nWarning: Not enough frequent numbers (found {len(frequent_numbers_pool)}) to generate 16-number combinations. Need at least 16.")
        else:
            generated_16_combos_set = set() # To ensure uniqueness
            attempts = 0
            max_attempts = NUM_16_NUMBER_CANDIDATES_TO_GENERATE * 5 # Try harder to get unique combos

            while len(generated_16_combos_set) < NUM_16_NUMBER_CANDIDATES_TO_GENERATE and attempts < max_attempts:
                attempts += 1
                # Ensure random.sample does not try to pick more items than available in the pool
                sample_size = min(16, len(frequent_numbers_pool))
                if sample_size < 16: # Should not happen if we passed the len(frequent_numbers_pool) < 16 check
                    break 
                
                candidate_16 = tuple(sorted(random.sample(frequent_numbers_pool, 16)))
                if candidate_16 not in generated_16_combos_set:
                    generated_16_combos_set.add(candidate_16)
                    avg_score = score_candidate_bet(list(candidate_16), number_frequency)
                    scored_16_number_candidates.append((avg_score, list(candidate_16)))
            
            print(f"\n--- 16-Number Candidates (Generated from Top {TOP_N_FREQUENT_NUMBERS} Frequent Numbers) ---")
            print(f"Total 16-number candidates generated: {len(scored_16_number_candidates)} (attempted {NUM_16_NUMBER_CANDIDATES_TO_GENERATE} unique)")
            if scored_16_number_candidates:
                scored_16_number_candidates.sort(key=lambda x: x[0], reverse=True)
                print("Top 5 scored 16-number candidates:")
                for i, (score, combo) in enumerate(scored_16_number_candidates[:5]):
                    print(f"  {i+1}. Avg Score: {score:.4f}, Combination: {sorted(combo)}")
            else:
                print("No 16-number candidates were generated or scored.")
        
        # Example test of score_candidate_bet with a 17-number combination (if needed)
        # if len(frequent_numbers_pool) >= 17:
        #     test_17_combo = frequent_numbers_pool[:17]
        #     avg_score_17 = score_candidate_bet(test_17_combo, number_frequency)
        #     num_sub_combos_17 = len(get_15_number_sub_combinations(test_17_combo))
        #     print(f"\nTest score for a 17-number combo {sorted(test_17_combo)} (from {num_sub_combos_17} sub-combos): {avg_score_17:.4f}")


    # Original test section for calculate_score (can be kept for detailed feature checking if desired)
    # print("\n--- Original Test Section for calculate_score ---")
    # test_combination_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] 
    # score1, details1 = calculate_score(test_combination_1, number_frequency if number_frequency else Counter())
    # print(f"\nTesting Combination 1: {test_combination_1} -> Total Score: {score1:.4f}")
    # for key, value in details1.items(): print(f"  {key}: {value}")
    
    print("\nNote: Normalization for freq_score is basic. Scores are relative.")
    print("COST_TABLE (first 2 items):", {k: COST_TABLE[k] for k in list(COST_TABLE)[:2]})
