import pandas as pd
import io # io might not be needed anymore if csv_data is removed
import requests
import json # Though requests.json() is often enough

# Commented out the existing hardcoded CSV data string
# csv_data = """Concurso,Data,Bola1,Bola2,Bola3,Bola4,Bola5,Bola6,Bola7,Bola8,Bola9,Bola10,Bola11,Bola12,Bola13,Bola14,Bola15,Arrecadacao_Total,Ganhadores_15_Numeros,Cidade_UF,Ganhadores_14_Numeros,Ganhadores_13_Numeros,Ganhadores_12_Numeros,Ganhadores_11_Numeros,Valor_Rateio_15_Numeros,Valor_Rateio_14_Numeros,Valor_Rateio_13_Numeros,Valor_Rateio_12_Numeros,Valor_Rateio_11_Numeros,Acumulado_15_Numeros,Estimativa_Premio,Valor_Acumulado_Especial
# ... (rest of the CSV data) ...
# """

# Define the Lotofácil cost table at the module level
COST_TABLE = {
    15: {"cost": 3.00, "combinations": 1},
    16: {"cost": 48.00, "combinations": 16},
    17: {"cost": 408.00, "combinations": 136},
    18: {"cost": 2448.00, "combinations": 816},
    19: {"cost": 11628.00, "combinations": 3876},
    20: {"cost": 46512.00, "combinations": 15504},
}

df_lotofacil = None # Initialize as None at module level
# bola_cols might be obsolete if API provides 'numeros_list' directly
# bola_cols = [f'Bola{i}' for i in range(1, 16)] 

def fetch_lotofacil_data_from_api():
    """
    Fetches Lotofácil data using a primary bulk endpoint, with a fallback to iterating
    through individual contest endpoints. Transforms data into a Pandas DataFrame.
    'numeros_list' is created directly with lists of integers.
    """
    BULK_API_URL = "https://loteriascaixa-api.herokuapp.com/api/lotofacil"
    INDIVIDUAL_API_URL_TEMPLATE = "https://loteriascaixa-api.herokuapp.com/api/lotofacil/{}"
    MAX_CONTESTS_TO_ITERATE = 3400 # As per subtask
    ITERATION_TIMEOUT = 5 # seconds for individual requests
    BULK_TIMEOUT = 20 # seconds for bulk request
    MIN_REQUESTS_FOR_FAILURE_CHECK = 100 # Min contests to check before assessing failure rate
    FAILURE_RATE_THRESHOLD = 0.10 # 10% failure rate threshold

    transformed_data = []
    df_from_api = None

    # 1. Primary Endpoint Attempt
    print(f"Attempting to fetch data from bulk endpoint: {BULK_API_URL}")
    try:
        response = requests.get(BULK_API_URL, timeout=BULK_TIMEOUT)
        response.raise_for_status()
        
        # Check if content type is JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            print(f"Bulk API Error: Unexpected Content-Type: {content_type}. Expected 'application/json'.")
            print("Response text (first 500 chars):", response.text[:500])
            raise ValueError("Bulk API did not return JSON.") # Will be caught by outer except

        api_data_list = response.json()
        if isinstance(api_data_list, list) and api_data_list: # Check if it's a non-empty list
            print(f"Successfully fetched data from bulk endpoint. Found {len(api_data_list)} items (potential draws).")
            # Now, parse this list of draws
            for draw_data in api_data_list:
                try:
                    # Adapt to common field names from this API: 'concurso', 'data', 'dezenas'
                    concurso = int(draw_data.get('concurso', draw_data.get('numero'))) # numero as fallback
                    data_str = draw_data.get('data')
                    dezenas_str_list = draw_data.get('dezenas') # Expecting a list of strings like ["01", "02"]

                    if concurso is None or data_str is None or dezenas_str_list is None:
                        print(f"Warning: Draw data from bulk API is missing key fields (concurso, data, or dezenas). Draw: {draw_data}. Skipping.")
                        continue
                    
                    numeros_int_list = [int(n) for n in dezenas_str_list]
                    transformed_data.append({
                        'Concurso': concurso,
                        'Data': data_str,
                        'numeros_list': numeros_int_list
                    })
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Error processing a draw from bulk API: {draw_data}. Error: {e}. Skipping.")
                    continue
            
            if transformed_data:
                df_from_api = pd.DataFrame(transformed_data)
                print(f"Successfully transformed {len(df_from_api)} draws from bulk API data.")
                return df_from_api # Success with bulk endpoint
            else:
                print("Bulk API data was a list, but no valid draws could be transformed. Attempting fallback...")
        else:
            print("Bulk endpoint did not return a list of all contests or returned an empty list. Attempting fallback...")

    except requests.exceptions.RequestException as e:
        print(f"Bulk API Request Error: {e}. Attempting fallback...")
    except (json.JSONDecodeError, ValueError) as e: # Catch JSON errors or ValueErrors from structure checks
        print(f"Bulk API JSON/Data Error: {e}. Attempting fallback...")
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred with bulk API: {e}. Attempting fallback...")


    # 2. Fallback Strategy (Iteration)
    print("\nInitiating fallback: fetching contests individually.")
    all_fetched_draws = []
    failed_requests_count = 0
    
    for concurso_numero in range(1, MAX_CONTESTS_TO_ITERATE + 1):
        individual_url = INDIVIDUAL_API_URL_TEMPLATE.format(concurso_numero)
        try:
            if concurso_numero % 200 == 0: # Print progress periodically
                 print(f"Fetching individual contest: {concurso_numero}/{MAX_CONTESTS_TO_ITERATE}...")
            
            response = requests.get(individual_url, timeout=ITERATION_TIMEOUT)
            response.raise_for_status() # Check for HTTP errors

            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                print(f"Warning: Contest {concurso_numero}: Unexpected Content-Type: {content_type}. Skipping.")
                failed_requests_count += 1
                continue

            draw_data = response.json()

            concurso = int(draw_data.get('concurso', draw_data.get('numero')))
            data_str = draw_data.get('data')
            dezenas_str_list = draw_data.get('dezenas')

            if concurso is None or data_str is None or dezenas_str_list is None:
                print(f"Warning: Contest {concurso_numero}: Data missing key fields. Skipping.")
                failed_requests_count += 1
                continue

            numeros_int_list = [int(n) for n in dezenas_str_list]
            all_fetched_draws.append({
                'Concurso': concurso,
                'Data': data_str,
                'numeros_list': numeros_int_list
            })

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Warning: Contest {concurso_numero} not found (404).")
            else:
                print(f"Warning: Contest {concurso_numero}: HTTP Error {e.response.status_code}.")
            failed_requests_count += 1
        except requests.exceptions.RequestException as e:
            print(f"Warning: Contest {concurso_numero}: Request Error {e}.")
            failed_requests_count += 1
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Contest {concurso_numero}: Error processing data: {e}. Skipping.")
            failed_requests_count += 1
        
        # Failure Threshold Check
        if concurso_numero >= MIN_REQUESTS_FOR_FAILURE_CHECK and \
           (failed_requests_count / concurso_numero) > FAILURE_RATE_THRESHOLD:
            print(f"Error: Stopping iteration for contest {concurso_numero} due to high failure rate ({failed_requests_count}/{concurso_numero} = {failed_requests_count / concurso_numero:.2%}).")
            break 
            
    if all_fetched_draws:
        print(f"\nSuccessfully fetched {len(all_fetched_draws)} contests via iteration out of {concurso_numero} attempts.")
        df_from_api = pd.DataFrame(all_fetched_draws)
        return df_from_api
    else:
        print("\nFallback iteration failed to fetch sufficient data or all attempts failed.")
        return None


def process_and_validate_numbers(df):
    """
    Validates 'numeros_list' (expected to be present and contain lists of numbers),
    ensures numbers are integers in 1-25 range, and filters the DataFrame
    to keep only rows with valid 15-number lists.
    """
    if df.empty:
        print("DataFrame is empty. Skipping processing and validation.")
        return df

    if 'numeros_list' not in df.columns:
        print("Error: 'numeros_list' column not found in DataFrame provided by API fetcher. Cannot proceed.")
        return pd.DataFrame() # Return empty if essential column is missing

    # Ensure numbers in numeros_list are integers and within 1-25 range
    # This step might be slightly redundant if API fetcher guarantees it, but good for robustness
    cleaned_numeros_list = []
    for num_list_item in df['numeros_list']:
        if isinstance(num_list_item, list):
            valid_numbers = [int(num) for num in num_list_item if isinstance(num, (int, float, str)) and str(num).isdigit() and 1 <= int(num) <= 25]
            cleaned_numeros_list.append(valid_numbers)
        else:
            cleaned_numeros_list.append([]) # If item is not a list, replace with empty list
    df['numeros_list'] = cleaned_numeros_list
    
    print("\n--- Validating 'numeros_list' (length and range 1-25 from API data) ---")
    # This validation logic now applies to 'numeros_list' however it was populated
    # Validation logic (similar to before, but now assumes 'numeros_list' came from API)
    all_valid_after_api_processing = True
    problematic_rows_from_api = []
    # Iterating using df.iterrows() to get index and row for .loc access if needed for 'Concurso'
    for index, row_data in df.iterrows():
        num_list_item = row_data['numeros_list']
        current_concurso_val = row_data.get('Concurso', 'N/A') # Use .get for safety

        if not isinstance(num_list_item, list) or len(num_list_item) != 15:
            all_valid_after_api_processing = False
            problematic_rows_from_api.append({
                "index": index, "concurso": current_concurso_val,
                "reason": f"Expected 15 numbers, got {len(num_list_item) if isinstance(num_list_item, list) else 'not a list'}",
                "numbers": num_list_item
            })
            continue
        for num_val in num_list_item:
            if not (isinstance(num_val, int) and 1 <= num_val <= 25):
                all_valid_after_api_processing = False
                problematic_rows_from_api.append({
                    "index": index, "concurso": current_concurso_val,
                    "reason": f"Invalid number {num_val} (type: {type(num_val).__name__} or not in 1-25 range)",
                    "numbers": num_list_item
                })
                break 

    if all_valid_after_api_processing:
        print("API Data Validation successful: All rows in 'numeros_list' have 15 valid numbers (1-25).")
    else:
        print("API Data Validation failed for some rows (before final DataFrame filtering):")
        for row_info_detail in problematic_rows_from_api:
            print(f"  Index: {row_info_detail['index']}, Concurso: {row_info_detail['concurso']}, Reason: {row_info_detail['reason']}, Numbers: {row_info_detail['numbers']}")
    print("--- API Data Validation Complete ---")
    
    original_row_count = len(df)
    # Filter DataFrame: keep rows where 'numeros_list' is a list of 15 valid integers
    df = df[df['numeros_list'].apply(
        lambda x: isinstance(x, list) and len(x) == 15 and all(isinstance(n, int) and 1 <= n <= 25 for n in x)
    )].copy()
    
    filtered_row_count = len(df)
    print(f"\nShape of DataFrame after API data processing & final row filtering: ({original_row_count}, {df.shape[1] if original_row_count > 0 and not df.empty else (original_row_count > 0 and df.columns.size or 'N/A')}) -> {df.shape}")
    print(f"{original_row_count - filtered_row_count} rows were removed by final filtering.")
    
    return df


def load_data():
    """
    Loads Lotofácil data from the Caixa API, then processes and validates the numbers.
    """
    df = fetch_lotofacil_data_from_api()

    if df is None or df.empty:
        print("Fetching from API failed or returned no data. Returning empty DataFrame.")
        return pd.DataFrame()

    # Proceed with processing and validation using the successfully fetched df
    # process_and_validate_numbers now expects 'numeros_list' to be present
    df = process_and_validate_numbers(df)
    return df


def print_data_info(df):
    """Prints head and info of the DataFrame and the cost table."""
    if not df.empty:
        print("\nDataFrame Head (Post-Processing):")
        # Displaying 'numeros_list' as well for verification
        # Show 'numeros_list' and some identifying columns like 'Concurso' if they exist
        cols_to_show = []
        if 'Concurso' in df.columns: cols_to_show.append('Concurso')
        
        # Removed BolaX or 'numeros' string column from head display as 'numeros_list' is the primary source now
        if 'Data' in df.columns: cols_to_show.append('Data')
        if 'numeros_list' in df.columns: cols_to_show.append('numeros_list')
        
        if not cols_to_show: 
            print(df.head()) # Fallback
        else:
            existing_cols_to_show = [col for col in cols_to_show if col in df.columns]
            if existing_cols_to_show:
                print(df[existing_cols_to_show].head())
            else:
                print(df.head()) # Fallback if somehow 'Concurso', 'Data', 'numeros_list' are all missing

        print("\nDataFrame Info (Post-Processing):")
        df.info() 
    else:
        print("\nDataFrame is empty after API fetching and processing.")

    print("\nLotofácil Cost Table:")
    for numbers, data in COST_TABLE.items():
        print(f"{numbers} numbers: R$ {data['cost']:.2f} ({data['combinations']} combinations)")


# Load data when the module is imported or run.
# This will now fetch from API.
df_lotofacil = load_data()

if __name__ == "__main__":
    # This will now print head/info of the API-fetched, processed, and filtered DataFrame
    print_data_info(df_lotofacil)
