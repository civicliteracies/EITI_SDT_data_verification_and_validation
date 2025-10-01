# Data Verification Summary

This document summarizes the data verification process performed in the `3_verify` directory. The goal of this process is to assess the quality of the consolidated EITI data and prepare it for the cleaning and mapping stages.

The verification process is divided into three main stages, each corresponding to a Jupyter notebook:

### 1. Completeness and Correctness (`01 - Completeness and correctness.ipynb`)

This stage focuses on identifying missing or incorrect data in the consolidated dataset.

-   **Checks Performed:**
    -   Searched for `NULL`, blank, or missing values in all tables.
    -   Identified text in fields that should be numeric.
-   **Key Findings:**
    -   Several tables, particularly those related to projects and companies, have a significant percentage of `NULL` values.
    -   Some countries are missing from certain data tables, indicating incomplete reporting.
    -   Specific columns with a high number of missing values were identified.

### 2. Duplication and Coherence (`02 - Duplication and coherence.ipynb`)

This stage checks for duplicate data and inconsistencies between different parts of the dataset.

-   **Checks Performed:**
    -   Identified potential duplicate rows within each table based on a combination of columns that should be unique.
    -   Compared the lists of companies, government agencies, and projects between the "Part 3" files and the transactional data in "Part 4" and "Part 5".
    -   Checked for consistency in reported revenue between government revenues (Part 4) and company data (Part 5).
-   **Key Findings:**
    -   A significant number of potential duplicate rows were found in most tables.
    -   There are discrepancies between the entities listed in the Part 3 tables and those in the transactional data.
    -   Inconsistencies were found in the computed revenue values between the government and company data for a majority of reports.

### 3. Declaration Generation (`03 - Generate declarations.ipynb`)

This stage separates the "clean" data from the problematic data identified in the previous steps.

-   **Process:**
    -   The notebooks identify and separate "red flag" (potentially duplicate or problematic) rows from the "non-red flag" rows.
    -   The "non-red flag" data is then used to generate individual "declaration" CSV files for each country and year.
-   **Output:** The output of this stage is a set of individual declaration files stored in the `2_get/declarations` directory. This separation of clean and problematic data allows for more focused data cleaning in the subsequent stages.
