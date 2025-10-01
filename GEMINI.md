# Gemini EITI Data Verification and Validation Analysis

This document outlines the structure and process of the EITI data verification and validation repository, as analyzed by the Gemini agent.

## Repository Structure

The repository is organized into five main directories, each representing a stage in the data processing pipeline:

1.  **`1_define`**: Contains placeholder documents that were intended to define the project's process and approach.
2.  **`2_get`**: This directory is for data acquisition and consolidation.
    *   `declarations`: Contains the raw, individual EITI data declarations, separated by country and year.
    *   `consolidated`: Contains the consolidated EITI data in several CSV files, as well as a Python script for further processing.
3.  **`3_verify`**: Includes Jupyter notebooks for data verification, focusing on completeness, correctness, duplication, and coherence. This stage also generates the initial "declaration" files.
4.  **`4_clean`**: This directory is dedicated to data cleaning and preparation for mapping to the Beneficial Ownership Data Standard (BODS).
    *   `1_data_preparation`: Contains notebooks for creating "ideal" lists of entities and preparing the data for cleaning.
    *   `2_data_editing`: Contains OpenRefine project files, indicating that OpenRefine was used for data cleaning. The `output` subdirectory contains the cleaned data, and a `versioning.md` file details the cleaning process.
    *   `3_bods_mapping`: Includes notebooks for reviewing and flattening the BODS schema, and a `mapping.csv` file that contains the flattened schema.
5.  **`5_publish`**: This directory is for publishing the final data.
    *   `1_test`: Contains notebooks for mapping the cleaned EITI data to BODS, creating a SQLite database, and some test data.
    *   `2_final`: Contains a placeholder file indicating that the final output is the SQLite database.

## Data Processing and Analysis Workflow

The repository follows a clear, step-by-step data processing workflow:

1.  **Data Acquisition and Consolidation (`2_get`)**:
    *   The process starts with individual EITI data declarations, which are then consolidated into a set of CSV files.
    *   A Python script (`add_gfs_to_comp_payments.py`) is used to analyze the feasibility of linking government finance statistics (GFS) to company payments and to propose a methodology for data enrichment.

2.  **Data Verification (`3_verify`)**:
    *   The consolidated data is verified for completeness, correctness, duplication, and coherence using a series of Jupyter notebooks.
    *   This stage identifies issues such as missing data, `NULL` values, and inconsistencies between different parts of the dataset.
    *   "Declaration" files are generated for each country and year, separating the "clean" data from the problematic data.

3.  **Data Cleaning (`4_clean`)**:
    *   The data is further cleaned and prepared for mapping to the BODS.
    *   "Ideal" lists of companies, government agencies, and projects are created based on the transactional data.
    *   OpenRefine was used for interactive data cleaning, with the cleaned data saved in the `4_clean/2_data_editing/output` directory.
    *   A `versioning.md` file in the `4_clean/2_data_editing/output` directory provides a detailed log of the cleaning steps.

4.  **BODS Mapping (`4_clean/3_bods_mapping`)**:
    *   The BODS JSON schema is reviewed and flattened into a tabular format (`mapping.csv`).
    *   This flattened schema is used as a reference for mapping the cleaned EITI data to the BODS.

5.  **Publishing (`5_publish`)**:
    *   The cleaned and mapped data is used to generate the final output of the project.
    *   The `eiti_bods_mapping.ipynb` notebook maps the EITI data to BODS, creating JSON statements for entities and relationships.
    *   The `eiti_data_db.ipynb` notebook is likely used to create the final SQLite database (`eiti_data.db`).
    *   The final output is the `eiti_data.db` database, which contains the cleaned, verified, and BODS-mapped EITI data.

## Key Findings

*   The repository demonstrates a rigorous and well-documented data processing pipeline.
*   The use of Jupyter notebooks and OpenRefine indicates a combination of automated and interactive data cleaning techniques.
*   The project's goal is to produce a clean, verified, and standardized dataset of EITI data in a SQLite database, mapped to the Beneficial Ownership Data Standard.
*   The `versioning.md` file and the various notebooks provide a high degree of transparency into the data cleaning and mapping process.
*   The final output is a SQLite database, which is a portable and accessible format for data analysis.
