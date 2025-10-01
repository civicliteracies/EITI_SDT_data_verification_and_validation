# Data Cleaning and Preparation Summary

This document summarizes the data cleaning and preparation process performed in the `4_clean` directory. The goal of this process is to clean, enrich, and standardize the EITI data to prepare it for mapping to the Beneficial Ownership Data Standard (BODS) and for publication.

The cleaning process is divided into three main stages:

### 1. Data Preparation (`1_data_preparation`)

This stage focuses on creating "ideal" lists of entities (companies, government agencies, and projects) and preparing the data for the main cleaning phase.

-   **Ideal and Actual Lists:** The notebooks in this directory compare the entity lists from the "Part 3" files with the transactional data in "Part 4" and "Part 5". This process identifies discrepancies and creates "complete" versions of the transactional data and "ideal" lists of entities.
-   **Output:** The output of this stage is a set of "ideal" and "complete" CSV files located in the `4_clean/1_data_preparation/data/outputs/` directory. These files serve as the direct input for the next stage of cleaning.

### 2. Data Editing (`2_data_editing`)

This stage involves detailed data cleaning and transformation using OpenRefine.

-   **OpenRefine Cleaning:** The data is cleaned using a series of operations documented in the OpenRefine history files. These operations include:
    -   Standardizing categorical values (e.g., country names, currency names, entity types).
    -   Cleaning text fields by removing extra whitespace and correcting typos.
    -   Enriching the data by adding new columns from other parts of the dataset.
    -   Renaming columns to a consistent snake_case format.
    -   Converting data types (e.g., to numeric or date formats).
    -   Handling missing values by replacing them with standardized representations ("n/a" or "n/v").
-   **Detailed History:** A detailed, step-by-step history of the cleaning operations for each part of the data can be found in the `4_clean/2_data_editing/openrefine/cleaning-history.md` file.
-   **Output:** The cleaned data is saved as a set of CSV files in the `4_clean/2_data_editing/output/` directory.

### 3. BODS Mapping Preparation (`3_bods_mapping`)

This stage prepares for the mapping of the cleaned EITI data to the Beneficial Ownership Data Standard (BODS).

-   **Schema Review and Flattening:** The BODS JSON schemas are reviewed and flattened into a tabular format (`mapping.csv`). This flattened schema serves as a reference for the mapping process.
-   **Output:** The main output of this stage is the `mapping.csv` file, which contains the flattened BODS schema.
