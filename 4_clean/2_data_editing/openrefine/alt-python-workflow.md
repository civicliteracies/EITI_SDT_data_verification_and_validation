# Alternative Python-Based Cleaning and Entity Resolution Workflow

This document outlines a recommended workflow for automating the EITI data cleaning and entity resolution process using Python, leveraging the existing cleaned data as a reference.

### Prerequisites: Preparing the New Data

Before starting this workflow, the new batch of data needs to be brought to a state similar to the consolidated files in the `2_get/consolidated` directory. This involves the following pre-processing steps:

1.  **Consolidation:** The individual report files for the new data batch should be consolidated into a set of single files (e.g., a new "Part 1", "Part 3", "Part 4", "Part 5", etc.).
2.  **Initial Verification:** It is recommended to perform the basic data quality and structural checks as outlined in the `3_verify` directory. This will help to catch any major errors or inconsistencies early on.

Once the new data is in this consolidated and verified state, it can be used as the input for the Python-based workflow described below.

## Overview

Instead of replicating the entire cleaning process from scratch, this workflow uses the existing cleaned files as a "master" or "lookup" dataset. This transforms the task from a complex data cleaning exercise into a more straightforward **entity resolution** problem. The process is divided into two main scripts and a manual review step.

### Script 1: `data_processing_and_review_generation.py`

This script is responsible for the initial processing of a new batch of data.

1.  **Load and Clean:**
    *   Loads the new data and the existing "golden record" data from the `4_clean/2_data_editing/output/` directory.
    *   Performs basic, easily automatable cleaning steps on the new data (e.g., trimming whitespace, converting to a consistent case).

2.  **Direct Matching:**
    *   Attempts to match the new records to the golden records using a composite key (e.g., `company_name` + `country` + `year`).
    *   For all direct matches, the existing `eiti_id` from the reference data is assigned.

3.  **Fuzzy Matching and Review File Generation:**
    *   For all records that do not have a direct match, the script performs fuzzy string matching (e.g., using the FuzzyWuzzy or rapidfuzz libraries) to find the top 2-3 most likely candidates from the golden records.
    *   It then generates a `review.csv` file with the following columns:
        *   `new_record_key`: A unique identifier for the new record.
        *   `new_record_name`: The name of the entity from the new data.
        *   `suggested_match_1_name`, `suggested_match_1_id`, `suggested_match_1_score`
        *   `suggested_match_2_name`, `suggested_match_2_id`, `suggested_match_2_score`
        *   ... (and so on for a few suggestions)
        *   **`action_to_take`**: An empty column for the user to fill in.
        *   **`confirmed_eiti_id`**: An empty column for the user to fill in.

### The Manual Review Step

This is the "human-in-the-loop" part of the process. A user opens the `review.csv` file and, for each row, fills in the `action_to_take` and `confirmed_eiti_id` columns based on the following actions:

-   `CONFIRM_MATCH`: If one of the suggestions is correct.
-   `NEW_ENTITY`: If the record is a new, valid entity.
-   `BAD_DATA`: If the record is invalid and should be discarded.
-   `MANUAL_ID`: If they know the correct `eiti_id` and it wasn't suggested.

### Script 2: `process_reviewed_data.py`

This script takes the human-reviewed `review.csv` file as its input and finalizes the cleaning process.

1.  **Process Reviewed Actions:**
    *   For rows with `action_to_take` as `CONFIRM_MATCH` or `MANUAL_ID`, it uses the value in the `confirmed_eiti_id` column to update the corresponding records in the new dataset.
    *   For rows with `action_to_take` as `NEW_ENTITY`, it generates a new UUID for the `eiti_id` and applies it to the new record. It then appends this new, confirmed entity to the "golden record" file, improving the reference data for future runs.
    *   For rows with `action_to_take` as `BAD_DATA`, it flags those records to be excluded from the final dataset.

2.  **Finalize Dataset:**
    *   The script then combines the records that were matched directly in the first script with the newly processed records from the reviewed file.
    *   The result is a fully cleaned and ID'd dataset, ready for the next stage of the data pipeline.