# OpenRefine Cleaning History

This document provides a detailed, step-by-step summary of the data cleaning operations performed on the EITI data using OpenRefine, as inferred from the project history files.

## Part 1: Report Metadata (`eiti-data_part1_1.3-history.json`)

### Standardization and Cleaning

- **Standardize `National currency name`:**
    - Merged "Ukrainian Hryvnia" and "Ukrainian hryvnia" to "Ukrainian Hryvnia".
    - Changed "Franc CFA d’Afrique de l’Ouest" to "West African CFA franc".
    - Changed "Franc CFA d’Afrique centrale" to "Central African CFA Franc".
    - Converted the entire column to title case for consistency.
- **Standardize `Country or area name`:**
    - Changed "Cote d'Ivoire" to "Ivory Coast".
- **Whitespace Removal:**
    - Trimmed leading and trailing whitespace from all columns.
    - Replaced multiple consecutive spaces with a single space in all columns.

### Column Renaming and Value Standardization

- **Column Renaming:** All columns were renamed to use a consistent snake_case format.
- **Value Standardization:**
    - `name_independent_administrator`: Filled blank values with "n/a" and replaced "Not applicable" with "n/v". Standardized various administrator names.
    - `eiti_report_publication_date`: Filled blank values with "n/a" and converted the column to date format.
    - `eiti_report_url`: Cleaned up non-URL values.
    - `government_systematic_disclosure`: Standardized values to "yes", "no", "partially", "n/a", and "n/v".
    - `has_an_eiti_report_been_prepared`: Standardized values to "yes", "no", and "partially".
    - `eiti_data_publication_date`: Filled blank and non-standard missing values with "n/a" or "n/v" and converted to date format.
    - `eiti_data_url`: Cleaned up non-URL values and standardized missing value representations.
    - `other_relevant_files`: Standardized values to "yes" and "partially".

## Part 3: Projects (`eiti-data_part3-projects_1.1-history.json`)

- **Key and ID Generation:**
    - Created a `composite_project` column by joining `Project name`, `Country`, and `Year` to create a unique identifier for each project within a report.
    - Generated a unique `eiti_id_project` for each project using a UUID.
- **Column Renaming:** All columns were renamed to snake_case.
- **Data Standardization and Cleaning:**
    - **`commodities`:** Corrected misspellings (e.g., "Or" to "Gold"), standardized names (e.g., "Oil Palm" to "Palm oil"), and replaced missing values ("Not available", "Not reported") with "n/a".
    - **`unit`:** Standardized units of measurement (e.g., "Toneladas métricas" to "Tonnes").
    - **`status`:** Converted all values to lowercase.
- **Data Type Conversion:** Converted `production_volume` and `production_value` to numeric types.
- **Structural Changes:**
    - Moved the `Project name` column to the beginning of the dataset.
    - Reordered all rows based on the `Project name`.
    - Filled missing values in `Project name` and `eiti_id_project` using `blank-down` and `fill-down` operations.

## Part 4: Government Revenues (`eiti-data_part4_1.1-history.json`)

- **Government Entity Standardization:**
    - The `Government entity` column was extensively cleaned by merging different variations of the same entity name into a single, consistent format.
- **Whitespace Removal:** Trimmed whitespace and collapsed multiple spaces in all columns.
- **Column Renaming:** Renamed all columns to snake_case.
- **Value Standardization:**
    - In the `sector` column, standardized "Oil & Gas" to "Oil and Gas".
    - Converted the `revenue_value` column to a numeric type and filled blank values with 0.
- **ID Generation:**
    - Created an `agency_key` by joining `government_entity`, `country`, and `year`.
    - Used this key to look up and add the `eiti_id_government` from the Part 3b data, creating a link between the datasets.

## Part 5: Company Data (`eiti-data_part5-0.11.6-history.json`)

- **Initial Cleanup:**
    - **Removed Columns:** `Company type`, `Company ID number`, `Sector`, `Commodities (comma-seperated)`, `Stock exchange listing or company website`, `Audited financial statement...`, `Payments to Governments Report`, and several duplicated columns (`Country2`, `ISO Code 2`, etc.).
    - **Renamed Columns:** Renamed `Company` to `company_name` and all other columns to snake_case.
- **Data Enrichment:**
    - Added `company_type`, `company_id`, `company_sector`, `company_commodities`, `company_public_listing_or_website`, and `company_audited_financial statement_or_equivalent` by creating a `composite_key` (`company_name`, `Country`, `Year`) and looking up values from the Part 3 data.
    - Added `project_name` and other project-related columns by looking up values from other project data.
    - Added `eiti_id_government` by looking up values from the Part 4 data.
- **Data Standardization and Cleaning:**
    - Standardized `company_type` to "Private" or "State-owned enterprises & public corporations".
    - Extensively cleaned the `company_commodities` column by correcting spellings, standardizing names, and handling various missing value representations.
    - Standardized boolean-like columns to "yes", "no", or "partially".
- **Data Type Conversion:** Converted `Revenue value` and `In-kind volume (if applicable)` to numeric types.
- **Handling Missing Values:** Filled blank values in numerous columns with "n/a" or "n/v" for consistency.
- **ID Generation:** Created a unique `eiti_id_company` for each company.
- **Final Structuring:** Reordered and removed temporary or redundant columns to finalize the dataset.
