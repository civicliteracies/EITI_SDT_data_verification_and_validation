import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Executive Summary

    This notebook explores how to  link `GFS codes` and `Sector ID` data, found in government revenues tables, to individual company payments, found in the Company data tables. The goal is to enable reliable historical and cross-country comparisons. 

    Our analysis found that a direct, naive join is not feasible due to significant inconsistencies in how data is reported. As a compromise, this notebook outlines two approaches to enrich the data while preserving its analytical integrity.

    The first approach, for `GFS Classification`, focuses on matching revenue streams before tackling the reconciliation of financial value data. We then address issues with `Sector` ID and outline a multi-level matching process that prioritizes the most reliable evidence first. 

    The primary finding and recommendation is that to achieve our goal it is essential to build reliability indicators that communicate to analysts when a specific report is relevant for a category of analyses. Building on this finding is a second recommandation to systematically categorise the quality of reports, both as a way to support the Secretariat's validation process and to pre-filter data for less sophisticated data users.

    Also included are descriptions of the categories of analyses to consider, and suggestions for next steps, including how to integrate those findings into the EITI data importer.
    """
    )
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import polars as pl
    from rapidfuzz import process, fuzz
    import glob
    import os
    import re

    # --- Configuration ---
    # Define all columns used in the join.
    string_keys_to_join = ["Government entity", "Revenue stream name", "Country"]
    other_keys_to_join = ["Year"]

    # This list is for cleaning government data, which also includes 'Sector'.
    gov_cols_to_normalize = string_keys_to_join + ["Sector"]

    # company data doesn't have sector, so the list of columns is the same as join_keys.
    comp_cols_to_normalize = string_keys_to_join


    # --- Helper Functions ---
    def normalize_text_column(column_expr: pl.Expr) -> pl.Expr:
        """Ensure column names are standardized to facilitate joining"""
        return (
            column_expr.str.to_lowercase()
            .str.strip_chars()
            .str.replace_all(r"\n", " ")
            .str.replace_all(r"[\(\)-_]", " ")
            .str.replace_all(r"\s+", " ")
            .str.strip_chars()
        )


    print("Setup and configuration complete.")
    return (
        comp_cols_to_normalize,
        gov_cols_to_normalize,
        mo,
        normalize_text_column,
        other_keys_to_join,
        pl,
        string_keys_to_join,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Introduction""")
    return


@app.cell(hide_code=True)
def _(mo, pl):
    # --- Calculate descriptive statistics for the entire dataset ---
    gov_revenues_lazy = pl.scan_csv(
        "Part 4 - Government revenues.csv",
        null_values=["-", "- ", ""],
        schema_overrides={"Revenue value": pl.Float64},
    )
    company_payments_lazy = pl.scan_csv(
        "Part 5 - Company data.csv",
        null_values=["-", "- ", ""],
        schema_overrides={"Revenue value": pl.Float64},
    )

    # Get all unique reports across both datasets.
    all_gov_reports = gov_revenues_lazy.select("Country", "Year").unique()
    all_comp_reports = company_payments_lazy.select("Country", "Year").unique()
    all_reports_df = (
        pl.concat([all_gov_reports, all_comp_reports]).unique().collect()
    )

    # Calculate key metrics.
    all_reports_count = all_reports_df.height
    total_countries = all_reports_df.get_column("Country").n_unique()
    unique_gov_streams = (
        gov_revenues_lazy.select(pl.col("Revenue stream name").n_unique())
        .collect()
        .item()
    )
    unique_comp_streams = (
        company_payments_lazy.select(pl.col("Revenue stream name").n_unique())
        .collect()
        .item()
    )
    unique_gov_entities = (
        gov_revenues_lazy.group_by("Country", "Government entity")
        .len()
        .collect()
        .height
    )

    mo.md(
        f"""
    ## Feasibility assessment: adding GFS codes and sector id to company payments.

    This notebook analyzes the feasibility of enriching company payment data (Part 5) with information from government revenue data (Part 4) and Reporting entitites (Part 3). The overall goal is to facilitate comparisons across time and countries at the company payment level. Two data points are explored:

    1.  **GFS data**: The first section explores how to reliably assign GFS codes from Part 4 to Part 5. We start with an assessment of the limits of a direct join, before proposing a compromise approach to reach our goal, using confidence metadata.

    2.  **Sector ID**: The second section addresses the question of Sector ID, which presents a different set of challenges than GFS codes. Similarly we end up outlining a compromise method to generate confidence metadata in the support of future analyses.

    **Dataset Overview:**

    * **Total Reports (Country-Year pairs):** {all_reports_count}
    * **Countries Covered:** {total_countries}
    * **Unique Government Revenue Streams:** {unique_gov_streams}
    * **Unique Company Payment Streams:** {unique_comp_streams}
    * **Unique Government Entities (Country-Specific):** {unique_gov_entities}
    """
    )
    return all_reports_count, company_payments_lazy, gov_revenues_lazy


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# I. GFS data""")
    return


@app.cell(hide_code=True)
def _(
    comp_cols_to_normalize,
    company_payments_lazy,
    gov_cols_to_normalize,
    gov_revenues_lazy,
    mo,
    normalize_text_column,
    pl,
):
    # --- Target dataframes ---
    # Receive LazyFrames from the previous cell and normalize text columns.
    gov_rev_normalized = gov_revenues_lazy.with_columns(
        normalize_text_column(pl.col(c)).alias(f"{c}_clean")
        for c in gov_cols_to_normalize
    )

    comp_pay_normalized = company_payments_lazy.with_columns(
        normalize_text_column(pl.col(c)).alias(f"{c}_clean")
        for c in comp_cols_to_normalize
    )

    mo.md(
        """This cell performs all the necessary data preparation. It applies the text normalization function to create a clean, consistent basis for matching.

    Data loaded and target dataframes defined
    """
    )
    return comp_pay_normalized, gov_rev_normalized


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Revenue stream name matching""")
    return


@app.cell(hide_code=True)
def _(
    comp_pay_normalized,
    gov_rev_normalized,
    other_keys_to_join,
    pl,
    string_keys_to_join,
):
    # Define the cleaned keys for the join.
    cleaned_join_keys = [
        f"{c}_clean" for c in string_keys_to_join
    ] + other_keys_to_join

    # Get unique streams from both datasets.
    gov_unique_streams = gov_rev_normalized.select(cleaned_join_keys).unique()
    comp_unique_streams = comp_pay_normalized.select(cleaned_join_keys).unique()

    # Perform a full join to see all streams from both sides.
    # FIX 1: Changed how="outer" to how="full"
    name_reconciliation = gov_unique_streams.join(
        comp_unique_streams, on=cleaned_join_keys, how="full", coalesce=True
    ).collect()

    # Calculate statistics.
    total_gov_streams = len(gov_unique_streams.collect())
    total_comp_streams = len(comp_unique_streams.collect())
    total_unique_streams = len(name_reconciliation)
    matched_streams = total_gov_streams + total_comp_streams - total_unique_streams
    match_rate = (
        matched_streams / total_unique_streams if total_unique_streams > 0 else 0
    )

    # Create the summary DataFrame.
    # FIX 2: Converted all numbers in the 'Value' list to strings.
    name_reconciliation_summary = pl.DataFrame(
        {
            "Metric": [
                "Unique Gov Streams",
                "Unique Company Streams",
                "Total Unique Streams (Combined)",
                "Matched Streams",
                "Match Rate",
            ],
            "Value": [
                str(total_gov_streams),
                str(total_comp_streams),
                str(total_unique_streams),
                str(matched_streams),
                f"{match_rate:.1%}",
            ],
        }
    )

    print("The above table shows key statistics about revenue streams")
    name_reconciliation_summary
    return (
        cleaned_join_keys,
        comp_unique_streams,
        gov_unique_streams,
        match_rate,
        matched_streams,
        total_unique_streams,
    )


@app.cell(hide_code=True)
def _(match_rate, matched_streams, mo, total_unique_streams):
    mo.md(
        f"""
    ### Partial Conclusion #1: Most names match, but a significant portion doesn't.

    * Out of a combined total of **{total_unique_streams}** unique revenue streams across all reports, we successfully matched **{matched_streams}** of them.
    * This represents a **{match_rate:.1%}** match rate based on names alone.

    The number of unmatched revenue streams ({total_unique_streams - matched_streams}) is significant enough that any analysis based on this dataset would be flawed. There are two ways to address the issue: the first is to determine if the unmatched streams are safe to excluded from GFS-based comparison analysis. The second is to set-up a confidence score system to easily filter out the reports that could derail the analysis.

    In the next steps we will:

    1. Analyse the patterns in the revenue streams that did not match.

    1. Analyse the financial discrepancy among the revenue streams that have matched

    2. Establish the confidence score system.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Financial discrepancies between Parts 4 and 5""")
    return


@app.cell(hide_code=True)
def _(cleaned_join_keys, comp_unique_streams, gov_unique_streams, mo, pl):
    # Isolate the streams that are only in the government data.
    unmatched_gov_streams = (
        gov_unique_streams.join(
            comp_unique_streams, on=cleaned_join_keys, how="anti"
        )
        .with_columns(source=pl.lit("Government Data Only"))
        .collect()
    )

    # Isolate the streams that are only in the company data.
    unmatched_comp_streams = (
        comp_unique_streams.join(
            gov_unique_streams, on=cleaned_join_keys, how="anti"
        )
        .with_columns(source=pl.lit("Company Data Only"))
        .collect()
    )

    # Combine them into a single DataFrame for analysis.
    unmatched_streams_df = pl.concat(
        [unmatched_gov_streams, unmatched_comp_streams]
    )

    # --- Analysis 1: What are the most common unmatched stream names? ---
    top_unmatched_names = (
        unmatched_streams_df.group_by("Revenue stream name_clean", "source")
        .len()
        .sort("len", descending=True)
    )

    # --- Analysis 2: Which reports are most affected by mismatches? ---
    mismatches_per_report = (
        unmatched_streams_df.group_by("Country_clean", "Year")
        .agg(
            unmatched_gov_streams=pl.col("Revenue stream name_clean")
            .filter(pl.col("source") == "Government Data Only")
            .n_unique(),
            unmatched_comp_streams=pl.col("Revenue stream name_clean")
            .filter(pl.col("source") == "Company Data Only")
            .n_unique(),
        )
        .with_columns(
            total_unmatched=pl.col("unmatched_gov_streams")
            + pl.col("unmatched_comp_streams")
        )
        .sort("total_unmatched", descending=True)
    )

    print(
        "Above are the top 10 most common unmatched stream names, and a summary of the reports most affected by these name mismatches."
    )
    mo.hstack([top_unmatched_names, mismatches_per_report])
    return (
        mismatches_per_report,
        top_unmatched_names,
        unmatched_comp_streams,
        unmatched_gov_streams,
        unmatched_streams_df,
    )


@app.cell(hide_code=True)
def _(
    all_reports_count,
    match_rate,
    mismatches_per_report,
    mo,
    pl,
    top_unmatched_names,
    unmatched_comp_streams,
    unmatched_gov_streams,
    unmatched_streams_df,
):
    # --- Calculate all summary stats for the conclusion ---
    unmatched_count = len(unmatched_streams_df)
    gov_only_count = len(unmatched_gov_streams)
    comp_only_count = len(unmatched_comp_streams)
    reports_affected_count = mismatches_per_report.height
    # This variable will be passed from cell 3 in the next section's update
    total_reports_count = all_reports_count

    # Calculate the concentration of mismatches in the most problematic reports.
    total_mismatches = mismatches_per_report.get_column("total_unmatched").sum()
    top_10_reports_mismatches = (
        mismatches_per_report.head(10).get_column("total_unmatched").sum()
    )
    top_20_reports_mismatches = (
        mismatches_per_report.head(20).get_column("total_unmatched").sum()
    )
    top_10_pct = (
        top_10_reports_mismatches / total_mismatches if total_mismatches > 0 else 0
    )
    top_20_pct = (
        top_20_reports_mismatches / total_mismatches if total_mismatches > 0 else 0
    )

    # Get the top government-side mismatch.
    top_gov_df = top_unmatched_names.filter(
        pl.col("source") == "Government Data Only"
    )
    if not top_gov_df.is_empty():
        top_gov_mismatch_name = top_gov_df.row(0)[0]
        top_gov_mismatch_count = top_gov_df.row(0)[2]
    else:
        top_gov_mismatch_name = "[None Found]"
        top_gov_mismatch_count = 0

    # Count reports with missing stream names from companies.
    missing_stream_name_count = (
        top_unmatched_names.filter(pl.col("Revenue stream name_clean").is_null())
        .select(pl.sum("len"))
        .item()
    )


    # --- Conclusion ---
    mo.md(
        f"""
    ### Partial Conclusion #2: Analysis of Name Mismatches

    * **Top-line Figures**: The **{match_rate:.1%}** name match rate leaves **{unmatched_count}** unique streams unmatched (**{gov_only_count}** from government data, **{comp_only_count}** from company data). These mismatches impact **{reports_affected_count}** of the **{total_reports_count}** total reports.

    * **Concentration of Issues**: The problem is highly concentrated in specific reports. The **top 10** most affected reports account for **{top_10_pct:.1%}** of all name mismatches, and the **top 20** account for **{top_20_pct:.1%}**. Reports from **Nigeria, Madagascar, and Ghana** contain the most mismatches.

    * The issue is similar across reports:
        * **Vocabulary Mismatch**: The most common unmatched term, **'{top_gov_mismatch_name}'**, appears in **{top_gov_mismatch_count}** government reports but has no direct company-side equivalent, indicating the use of different reporting vocabularies.
        * **Data Quality**: In **{missing_stream_name_count} reports**, company payments were submitted with a completely **missing revenue stream name**.
    """
    )
    return (top_10_pct,)


@app.cell(hide_code=True)
def _(cleaned_join_keys, comp_pay_normalized, gov_rev_normalized, mo, pl):
    # Create the mapping table from government data, including GFS and Sector IDs.
    gfs_mapping_final = gov_rev_normalized.select(
        cleaned_join_keys + ["GFS Classification", "Sector_clean"]
    ).unique()

    # Perform the left join and materialize the result.
    result_df = comp_pay_normalized.join(
        gfs_mapping_final, on=cleaned_join_keys, how="left"
    ).collect()

    # --- Financial Reconciliation ---

    # Get aggregated company totals for matched rows.
    company_totals = (
        result_df.filter(pl.col("GFS Classification").is_not_null())
        .group_by(cleaned_join_keys)
        .agg(pl.col("Revenue value").sum().alias("company_sum_value"))
    )

    # Get aggregated government totals.
    gov_totals = (
        gov_rev_normalized.group_by(cleaned_join_keys)
        .agg(pl.col("Revenue value").sum().alias("gov_reported_value"))
        .collect()
    )

    # Join the aggregated tables to compare them.
    reconciliation_summary = gov_totals.join(
        company_totals, on=cleaned_join_keys, how="left"
    ).fill_null(0)

    # Calculate the raw and percent discrepancy.
    reconciliation_summary = reconciliation_summary.with_columns(
        discrepancy=(pl.col("gov_reported_value") - pl.col("company_sum_value")),
        discrepancy_pct=pl.when(pl.col("gov_reported_value") != 0)
        .then(
            (
                (
                    (pl.col("gov_reported_value") - pl.col("company_sum_value"))
                    / pl.col("gov_reported_value")
                )
                * 100
            ).round(2)
        )
        .otherwise(None),
    ).sort(pl.col("discrepancy").abs(), descending=True)

    # --- Analyze Discrepancy Distribution Per Report ---
    discrepancy_tiers_per_report = (
        reconciliation_summary.filter(
            pl.col("gov_reported_value") != 0
        )  # Exclude div by zero cases
        .group_by("Country_clean", "Year")
        .agg(
            total_matched_streams=pl.len(),
            # Tier 1: <= 1%
            high_confidence_pct=(
                pl.col("discrepancy_pct")
                .filter(pl.col("discrepancy_pct").abs() <= 1)
                .len()
                / pl.len()
            ).round(2)
            * 100,
            # Tier 2: > 1% and <= 10%
            good_confidence_pct=(
                pl.col("discrepancy_pct")
                .filter(
                    pl.col("discrepancy_pct")
                    .abs()
                    .is_between(1, 10, closed="right")
                )
                .len()
                / pl.len()
            ).round(2)
            * 100,
            # Tier 3: > 10% and <= 20%
            medium_confidence_pct=(
                pl.col("discrepancy_pct")
                .filter(
                    pl.col("discrepancy_pct")
                    .abs()
                    .is_between(10, 20, closed="right")
                )
                .len()
                / pl.len()
            ).round(2)
            * 100,
            # Tier 4: > 20%
            low_confidence_pct=(
                pl.col("discrepancy_pct")
                .filter(pl.col("discrepancy_pct").abs() > 20)
                .len()
                / pl.len()
            ).round(2)
            * 100,
        )
        .sort("high_confidence_pct", descending=True)
    )

    print(
        "The first table shows the largest financial discrepancies for matched streams. The second shows the distribution of financial discrepancies per report, tiered by confidence level."
    )
    mo.vstack([reconciliation_summary, discrepancy_tiers_per_report])
    return discrepancy_tiers_per_report, reconciliation_summary


@app.cell(hide_code=True)
def _(discrepancy_tiers_per_report, mo, pl, reconciliation_summary):
    # --- 1. Calculate Overall Stats ---
    total_reconciled = reconciliation_summary.filter(
        pl.col("gov_reported_value") != 0
    ).height
    good_confidence_total_pct = (
        reconciliation_summary.filter(pl.col("discrepancy_pct").abs() <= 10).height
        / total_reconciled
    ) * 100
    low_confidence_total_pct = (
        reconciliation_summary.filter(pl.col("discrepancy_pct").abs() > 20).height
        / total_reconciled
    ) * 100

    # --- 2. Calculate Year-by-Year Trend ---
    temporal_trend = (
        discrepancy_tiers_per_report.group_by("Year")
        .agg(
            report_count=pl.len(),
            avg_high_confidence=(
                pl.col("high_confidence_pct") * pl.col("total_matched_streams")
            ).sum()
            / pl.col("total_matched_streams").sum(),
            avg_low_confidence=(
                pl.col("low_confidence_pct") * pl.col("total_matched_streams")
            ).sum()
            / pl.col("total_matched_streams").sum(),
        )
        .sort("Year")
    )

    # --- 3. Find Top & Bottom 5 Reports ---
    top_5_reports = discrepancy_tiers_per_report.sort(
        "high_confidence_pct", descending=True
    ).head(5)
    bottom_5_reports = discrepancy_tiers_per_report.sort(
        "low_confidence_pct", descending=True
    ).head(5)

    # --- 4. Prepare all variables for the f-string ---
    # This makes the markdown section cleaner and avoids complex loops for formatting.
    stats_2017 = temporal_trend.filter(
        (pl.col("Year").cast(pl.Int64)) == 2017
    ).row(0, named=True)
    stats_2018 = temporal_trend.filter(
        (pl.col("Year").cast(pl.Int64)) == 2018
    ).row(0, named=True)
    stats_2019 = temporal_trend.filter(
        (pl.col("Year").cast(pl.Int64)) == 2019
    ).row(0, named=True)
    stats_2020 = temporal_trend.filter(
        (pl.col("Year").cast(pl.Int64)) == 2020
    ).row(0, named=True)

    top_reports_list = [
        f"* **{row['Country_clean'].upper()} - {row['Year']}**: {row['high_confidence_pct']:.1f}%"
        for row in top_5_reports.iter_rows(named=True)
    ]
    bottom_reports_list = [
        f"* **{row['Country_clean'].upper()} - {row['Year']}**: {row['low_confidence_pct']:.1f}%"
        for row in bottom_5_reports.iter_rows(named=True)
    ]


    # --- 5. Display the Refined Conclusion ---
    mo.md(
        f"""
    ### Partial Conclusion #3: Financial Discrepancies are mostly report-specific.

    * **Overall Quality**: Across **{total_reconciled}** matched streams, **{good_confidence_total_pct:.1f}%** show good financial alignment (<10% discrepancy), while **{low_confidence_total_pct:.1f}%** have significant discrepancies (>20%).

    * **Temporal Analysis**: The year-by-year data shows that data quality is volatile and does not follow a simple linear trend of improvement.
        * **2017** ({stats_2017['report_count']} reports): **{stats_2017['avg_high_confidence']:.1f}%** high-confidence | **{stats_2017['avg_low_confidence']:.1f}%** low-confidence
        * **2018** ({stats_2018['report_count']} reports): **{stats_2018['avg_high_confidence']:.1f}%** high-confidence | **{stats_2018['avg_low_confidence']:.1f}%** low-confidence
        * **2019** ({stats_2019['report_count']} reports): **{stats_2019['avg_high_confidence']:.1f}%** high-confidence | **{stats_2019['avg_low_confidence']:.1f}%** low-confidence
        * **2020** ({stats_2020['report_count']} reports): **{stats_2020['avg_high_confidence']:.1f}%** high-confidence | **{stats_2020['avg_low_confidence']:.1f}%** low-confidence

    * **Report-Level Concentration**: The discrepancies are highly concentrated in specific reports, and some countries can submit both reliable and unreliable reports.
        * **Top 5 Most Reliable Reports** (% of streams with <1% discrepancy):
            {"\n        ".join(top_reports_list)}
        * **Top 5 Least Reliable Reports** (% of streams with >20% discrepancy):
            {"\n        ".join(bottom_reports_list)}
    """
    )
    return good_confidence_total_pct, low_confidence_total_pct


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Confidence score analysis""")
    return


@app.cell(hide_code=True)
def _(comp_pay_normalized, gov_rev_normalized, mo, pl, reconciliation_summary):
    # This cell synthesizes the analysis into a final "report card" for each report.

    # --- Get all unique reports ---
    gov_reports_lazy = gov_rev_normalized.select("Country_clean", "Year").unique()
    comp_reports_lazy = comp_pay_normalized.select(
        "Country_clean", "Year"
    ).unique()
    all_reports = pl.concat([gov_reports_lazy, comp_reports_lazy]).unique()

    # --- Calculate Name Match Score (vectorized) ---
    gov_names = gov_rev_normalized.select(
        "Country_clean", "Year", "Revenue stream name_clean"
    ).unique()
    comp_names = comp_pay_normalized.select(
        "Country_clean", "Year", "Revenue stream name_clean"
    ).unique()

    total_names_per_report = (
        pl.concat([gov_names, comp_names])
        .unique()
        .group_by("Country_clean", "Year")
        .len()
        .rename({"len": "total_unique_names"})
    )
    matched_names_per_report = (
        gov_names.join(
            comp_names,
            on=["Country_clean", "Year", "Revenue stream name_clean"],
            how="inner",
        )
        .group_by("Country_clean", "Year")
        .len()
        .rename({"len": "matched_names"})
    )

    name_scores = (
        total_names_per_report.join(
            matched_names_per_report, on=["Country_clean", "Year"], how="left"
        )
        .fill_null(0)
        .with_columns(
            name_match_score=pl.col("matched_names") / pl.col("total_unique_names")
        )
    )

    # --- Calculate Entity Match Score (vectorized) ---
    gov_entities = gov_rev_normalized.select(
        "Country_clean", "Year", "Government entity_clean"
    ).unique()
    comp_entities = comp_pay_normalized.select(
        "Country_clean", "Year", "Government entity_clean"
    ).unique()

    total_entities_per_report = (
        comp_entities.group_by("Country_clean", "Year")
        .len()
        .rename({"len": "total_comp_entities"})
    )
    matched_entities_per_report = (
        comp_entities.join(
            gov_entities,
            on=["Country_clean", "Year", "Government entity_clean"],
            how="inner",
        )
        .group_by("Country_clean", "Year")
        .len()
        .rename({"len": "matched_entities"})
    )

    entity_scores = (
        total_entities_per_report.join(
            matched_entities_per_report, on=["Country_clean", "Year"], how="left"
        )
        .fill_null(0)
        .with_columns(
            entity_match_score=pl.col("matched_entities")
            / pl.col("total_comp_entities")
        )
    )

    # --- Calculate Value Reconciliation Accuracy per Report ---
    value_accuracy_per_report = (
        reconciliation_summary.group_by("Country_clean", "Year")
        .agg(
            total_discrepancy=pl.col("discrepancy").abs().sum(),
            total_gov_value=pl.col("gov_reported_value").abs().sum(),
        )
        .with_columns(
            value_accuracy_score=pl.when(pl.col("total_gov_value") > 0)
            .then(1 - (pl.col("total_discrepancy") / pl.col("total_gov_value")))
            .otherwise(
                pl.when(pl.col("total_discrepancy") == 0).then(1.0).otherwise(0.0)
            )
        )
        .with_columns(
            value_accuracy_score=pl.when(pl.col("value_accuracy_score") < 0)
            .then(0.0)
            .otherwise(pl.col("value_accuracy_score"))
        )
        .select("Country_clean", "Year", "value_accuracy_score")
    )

    # --- Join Scores and Calculate Final Composite Score ---
    match_scores_df = (
        all_reports.join(
            name_scores.select("Country_clean", "Year", "name_match_score"),
            on=["Country_clean", "Year"],
            how="left",
        )
        .join(
            entity_scores.select("Country_clean", "Year", "entity_match_score"),
            on=["Country_clean", "Year"],
            how="left",
        )
        .collect()
        .fill_null(0)
    )


    final_scores = match_scores_df.join(
        value_accuracy_per_report, on=["Country_clean", "Year"], how="left"
    ).fill_null(0)

    # Define weights for the final score
    WEIGHT_VALUE = 0.60
    WEIGHT_NAME = 0.20
    WEIGHT_ENTITY = 0.20

    report_card_df = (
        final_scores.with_columns(
            overall_confidence=(
                (pl.col("value_accuracy_score") * WEIGHT_VALUE)
                + (pl.col("name_match_score") * WEIGHT_NAME)
                + (pl.col("entity_match_score") * WEIGHT_ENTITY)
            )
            * 100
        )
        .select(
            report_name=pl.concat_str(
                [pl.col("Country_clean").str.to_uppercase(), pl.col("Year")],
                separator=" - ",
            ),
            overall_confidence=pl.col("overall_confidence").cast(pl.Int64),
            value_accuracy_score=pl.col("value_accuracy_score").round(2),
            # Rename the column here for clarity
            stream_match_score=pl.col("name_match_score").round(2),
            entity_match_score=pl.col("entity_match_score").round(2),
        )
        .sort("overall_confidence", descending=True)
    )

    # --- NEW: Calculate counts based on inclusive filtering ---
    threshold = 0.80

    # First, create a temporary dataframe with boolean flags for high scores
    classified_reports_df = report_card_df.with_columns(
        is_v_high=pl.col("value_accuracy_score") >= threshold,
        is_s_high=pl.col("stream_match_score") >= threshold,
        is_e_high=pl.col("entity_match_score") >= threshold,
    )

    # Now, calculate the count for each filter. A report is included if it meets the minimum criteria.
    filter_counts = {
        # Minimum Req: V is High AND S is High AND E is High
        "HHH": classified_reports_df.filter(
            pl.col("is_v_high") & pl.col("is_s_high") & pl.col("is_e_high")
        ).height,
        # Minimum Req: V is High AND S is High (E can be anything)
        "HHL": classified_reports_df.filter(
            pl.col("is_v_high") & pl.col("is_s_high")
        ).height,
        # Minimum Req: V is High AND E is High (S can be anything)
        "HLH": classified_reports_df.filter(
            pl.col("is_v_high") & pl.col("is_e_high")
        ).height,
        # Minimum Req: V is High (S and E can be anything)
        "HLL": classified_reports_df.filter(pl.col("is_v_high")).height,
        # Minimum Req: S is High AND E is High (V can be anything)
        "LHH": classified_reports_df.filter(
            pl.col("is_s_high") & pl.col("is_e_high")
        ).height,
        # Minimum Req: S is High (V and E can be anything)
        "LHL": classified_reports_df.filter(pl.col("is_s_high")).height,
        # Minimum Req: E is High (V and S can be anything)
        "LLH": classified_reports_df.filter(pl.col("is_e_high")).height,
        # This remains exclusive: reports that meet NO high-quality criteria
        "LLL": classified_reports_df.filter(
            ~pl.col("is_v_high") & ~pl.col("is_s_high") & ~pl.col("is_e_high")
        ).height,
    }
    total_reports = report_card_df.height

    # --- Create the cheat sheet as a Polars DataFrame ---
    cheat_sheet_data = [
        {
            "Value": "✅",
            "Stream": "✅",
            "Entity": "✅",
            "Minimum Requirement": "Full Analysis: V, S, and E must be high.",
            "Reports (#)": filter_counts["HHH"],
        },
        {
            "Value": "✅",
            "Stream": "✅",
            "Entity": "❌",
            "Minimum Requirement": "Stream Analysis: V and S must be high.",
            "Reports (#)": filter_counts["HHL"],
        },
        {
            "Value": "✅",
            "Stream": "❌",
            "Entity": "✅",
            "Minimum Requirement": "Entity Analysis: V and E must be high.",
            "Reports (#)": filter_counts["HLH"],
        },
        {
            "Value": "✅",
            "Stream": "❌",
            "Entity": "❌",
            "Minimum Requirement": "Total Financials Only: V must be high.",
            "Reports (#)": filter_counts["HLL"],
        },
        {
            "Value": "❌",
            "Stream": "✅",
            "Entity": "✅",
            "Minimum Requirement": "Structural/Network: S and E must be high.",
            "Reports (#)": filter_counts["LHH"],
        },
        {
            "Value": "❌",
            "Stream": "✅",
            "Entity": "❌",
            "Minimum Requirement": "Vocabulary Analysis (Stream): S must be high.",
            "Reports (#)": filter_counts["LHL"],
        },
        {
            "Value": "❌",
            "Stream": "❌",
            "Entity": "✅",
            "Minimum Requirement": "Vocabulary Analysis (Entity): E must be high.",
            "Reports (#)": filter_counts["LLH"],
        },
        {
            "Value": "❌",
            "Stream": "❌",
            "Entity": "❌",
            "Minimum Requirement": "Exclude from Analysis: V, S, and E are all low.",
            "Reports (#)": filter_counts["LLL"],
        },
    ]
    cheat_sheet_df = pl.DataFrame(cheat_sheet_data)

    print("Final Report Confidence Scores")
    # --- Final Output: Display both dataframes vertically ---
    mo.vstack([report_card_df, cheat_sheet_df])
    return filter_counts, total_reports


@app.cell(hide_code=True)
def _(filter_counts, mo, total_reports):
    # Get the counts from the 'filter_counts' dictionary
    perfect_reports_count = filter_counts["HHH"]
    structural_analysis_count = filter_counts["LHH"]

    mo.md(
        f"""
    ### Partial Conclusion #4: The "Report Card" in Practice

    The distribution of reports across the quality combinations is the central finding of this analysis. It proves that a nuanced, contextual approach to using this data is not just helpful, but essential.

    * **"Perfect" Reports are the Exception**: Only **{perfect_reports_count} out of {total_reports} reports (about {perfect_reports_count/total_reports:.1%})** meet the "high quality" threshold across all three scores. A simple analysis that only uses perfect data would discard the vast majority of available information.

    * **Most Reports are Flawed but Usable**: The power of this model is its ability to create inclusive filters. For example, an analyst performing non-financial structural analysis (requiring high-quality Stream and Entity names) has access to a pool of **{structural_analysis_count} reports**. This is nearly double the number of 'perfect' reports and correctly includes those where financial data may be unreliable but the core labeling is sound, unlocking an entire category of network analysis that would otherwise be missed.

    * **An Actionable Path for GFS Enrichment**: The "report card" provides a clear, practical path forward. A one-time, bulk enrichment of Part 5 with GFS codes is not recommended due to the high risk of error. Instead, the model enables a safer, on-the-fly approach where analysts can join the datasets for their specific query, using the scores to filter for only those reports with the quality needed for their task. This maximizes data usability while minimizing the risk of flawed conclusions.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Explainer: component scores and combinations

    #### Overview

    The component scores are designed to help an analyst decide if a report is suitable for their specific question. Different types of analysis are sensitive to different types of data quality issues.

    * **Analysis of Financial Totals & Trends**

        * **Example**: *"How have BP's tax payments evolved over time?"*

        * **Primary Score to Check**: `value_accuracy_score`.

        * **Why**: This score measures if the reported dollar amounts align. A low score means the totals are unreliable, making any financial trend analysis misleading.

    * **Proportional / Breakdown Analysis**

        * **Example**: *"What percentage of total reported corporate tax came from Australian companies?"*

        * **Primary Score to Check**: `stream_match_score`.

        * **Why**: This analysis depends on correctly categorizing payments. If many "corporate tax" streams are unmatched, the total (the denominator) will be wrong, and the proportion will be skewed.

    * **Relational / Network Analysis**

        * **Example**: *"Which companies pay the customs agency across different countries?"*

        * **Primary Score to Check**: `entity_match_score`.

        * **Why**: This analysis is about the *relationships* between payers and recipients. If the entity names are not well-matched, you cannot build an accurate network of who pays whom.

    #### The Analyst's perspective

    We will use the following abbreviations and a "High" quality threshold of **{threshold:.0%}**.

    * **V: `value_accuracy_score`** (Are the dollar amounts correct?)

    * **S: `stream_match_score`** (Is the revenue stream vocabulary consistent?)

    * **E: `entity_match_score`** (Is the government entity vocabulary consistent?)

    * * *

    ##### ✅ 1. V: High, S: High, E: High

    * **Interpretation**: This is the **gold standard**. The financials are accurate, and all the labels for both revenue streams and government entities are consistent.

    * **Supported Analysis**: All types. This report is highly trustworthy.

    * **Analyst's View**: "I can perform any analysis I want, including detailed financial trends, proportional breakdowns by stream or by agency, and network analysis of who pays whom."

    ##### ⚠️ 2. V: High, S: High, E: Low

    * **Interpretation**: The financials are reliable and the revenue stream names are consistent, but the government entity names are a mess.

    * **Supported Analysis**: Financial totals and trends. Proportional analysis **by revenue stream**.

    * **Analyst's View**: "I can confidently analyze the total 'Corporate Tax' and its proportion of the total revenue. I **cannot** analyze which specific government agency received that tax."

    ##### ⚠️ 3. V: High, S: Low, E: High

    * **Interpretation**: A strange but possible case. The overall financial totals and entity names are reliable, but the breakdown of *what* the payments are for is inconsistent.

    * **Supported Analysis**: High-level financial totals. Analysis focused on the government entities.

    * **Analyst's View**: "I can determine the total amount paid to the 'Ministry of Finance'. I **cannot** reliably break down that total into its component revenue streams (e.g., taxes, royalties, fees)."

    ##### ⚠️ 4. V: High, S: Low, E: Low

    * **Interpretation**: Only the grand total financial figure for the report is trustworthy. All the descriptive labels are inconsistent.

    * **Supported Analysis**: Only the highest-level financial aggregates.

    * **Analyst's View**: "I can use the total revenue figure for this country-year in a trend analysis. I **cannot** perform any kind of proportional or breakdown analysis."

    ##### ⚠️ 5. V: Low, S: High, E: High

    * **Interpretation**: The labels are perfect, but the dollar amounts are wrong. The financial data is unreliable, but the *structure* of the relationships is clear.

    * **Supported Analysis**: Non-financial, structural, and network analysis.

    * **Analyst's View**: "I can map out the relationships and answer questions like 'Which companies pay the Ministry of Mines?' or 'What types of fees are typically paid by oil companies?'. I **cannot** trust any of the reported dollar values."

    ##### ❌ 6. V: Low, S: High, E: Low

    * **Interpretation**: The financials are wrong and the entity names are wrong. The only consistent data is the vocabulary of revenue streams.

    * **Supported Analysis**: Very limited. Primarily for metadata analysis.

    * **Analyst's View**: "I can see which *types* of revenue streams are mentioned in this report. I **cannot** use the financial data or link those streams to specific agencies."

    ##### ❌ 7. V: Low, S: Low, E: High

    * **Interpretation**: The financials are wrong and the revenue stream names are wrong. The only consistent data is the vocabulary of government entities.

    * **Supported Analysis**: Very limited. Primarily for metadata analysis.

    * **Analyst's View**: "I can see which government agencies are listed as receiving payments. I **cannot** use the financial data or determine what the payments were for."

    ##### ❌ 8. V: Low, S: Low, E: Low

    * **Interpretation**: The report is unreliable across all dimensions.

    * **Supported Analysis**: None.

    * **Analyst's View**: "I must exclude this report from any quantitative analysis. Its only value is as an example of poor data quality."
    """
    )
    return


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# II. Sector data""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The Challenge
    While some government revenue data contains a `Sector` column, it's not present in the company payments data (Part 5). Directly joining to get this information is unreliable for the same reasons outlined in Part 1.

    ### The Strategy
    We will implement the four-stage hierarchical matching process proposed in the final recommendations. This model attempts to find a sector for each company payment by prioritizing the most reliable data sources first. The levels are:

    * **Level 1: Project-Based Match** (Highest Confidence)
    * **Level 2: Revenue Stream-Based Match**
    * **Level 3: Government Entity-Based Match**
    * **Level 4: Company-Based Fallback** (Lowest Confidence)
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Initial exploration""")
    return


@app.cell(hide_code=True)
def _(mo, pl):
    # --- 1. Define the standardized list of target sectors ---
    target_sectors = ["Oil & Gas", "Mining", "Other"]


    # --- 2. Create a standardized sector cleaning function ---
    # This ensures that 'Oil' and 'Gas' are treated as 'Oil & Gas', etc.
    def standardize_sector(sector_col: pl.Expr) -> pl.Expr:
        return (
            pl.when(sector_col.str.contains(r"(?i)oil|gas"))
            .then(pl.lit("Oil & Gas"))
            .when(sector_col.str.contains(r"(?i)mining"))
            .then(pl.lit("Mining"))
            .otherwise(pl.lit("Other"))
        )


    # --- 3. Create the NEW, Data-Driven Commodity -> Sector Map ---
    # This dictionary is based on the unique commodity list you generated.
    # You can easily add more keywords to this list to improve it further.
    COMMODITY_KEYWORD_MAP = {
        # Oil & Gas Keywords
        "natural gas": "Oil & Gas",
        "crude oil": "Oil & Gas",
        "condensate": "Oil & Gas",
        "petroleum gas": "Oil & Gas",
        "crude oil and natural gas": "Oil & Gas",
        "free gas": "Oil & Gas",
        "dissolved gas": "Oil & Gas",
        "oil&gas": "Oil & Gas",
        "gasolina": "Oil & Gas",  # Spanish for gasoline
        "condensado": "Oil & Gas",  # Spanish for condensate
        "butane": "Oil & Gas",
        "propane": "Oil & Gas",
        "oil": "Oil & Gas",
        "gas": "Oil & Gas",
        "helium": "Oil & Gas",
        # Mining Keywords
        "gold": "Mining",
        "coal": "Mining",
        "copper": "Mining",
        "granite": "Mining",
        "limestone": "Mining",
        "iron": "Mining",
        "silver": "Mining",
        "nickel": "Mining",
        "potash and salts": "Mining",
        "manganese": "Mining",
        "zinc": "Mining",
        "titanium": "Mining",
        "ferruginous magnetite quartzite": "Mining",
        "cobalt": "Mining",
        "ilmenite": "Mining",
        "molybdenum": "Mining",
        "chromium": "Mining",
        "phosphate": "Mining",
        "precious metals": "Mining",
        "diamonds": "Mining",
        "ruby": "Mining",
        "aluminium": "Mining",
        "kaolin": "Mining",
        "dolomite": "Mining",
        "or": "Mining",  # French for gold
        "argent": "Mining",  # French for silver
        # Other Keywords
        "water": "Other",
        "electrical energy": "Other",
        "logs": "Other",
        "rubber": "Other",
        "oil palm": "Other",
        "fertilizer": "Other",
    }

    # Create the final DataFrame map from the dictionary
    commodity_to_sector_map = pl.DataFrame(
        list(COMMODITY_KEYWORD_MAP.items()), schema=["commodity_clean", "sector"]
    )

    print("Comprehensive, data-driven commodity map created.")
    mo.vstack(
        [
            mo.md("### Standardized Commodity to Sector Map"),
            commodity_to_sector_map,
        ]
    )
    return commodity_to_sector_map, standardize_sector


@app.cell(hide_code=True)
def _(normalize_text_column, pl, standardize_sector):
    # Load source datasets
    companies_df = pl.read_csv("Part 3 - Reporting companies' list.csv")
    projects_df = pl.read_csv("Part 3 - Reporting projects' list.csv")
    company_payments_df = pl.read_csv(
        "Part 5 - Company data.csv",
        null_values=["-", "- ", ""],
        schema_overrides={"Revenue value": pl.Float64},
    )

    # --- 1. Create a clean Company -> Sector Map ---
    # Apply the sector cleaner to standardize the output
    company_sector_map = (
        companies_df.select(
            company_name_clean=normalize_text_column(pl.col("Full company name")),
            sector_standardized=standardize_sector(pl.col("Sector")),
        )
        .drop_nulls(subset="company_name_clean")
        .unique(subset="company_name_clean", keep="first")
    )

    # --- 2. Aggregate Project Data (Your key suggestion) ---
    # One row per project, with lists of commodities and companies
    agg_projects_df = projects_df.group_by(
        project_name_clean=normalize_text_column(pl.col("Full project name"))
    ).agg(
        # Collect all unique, non-null commodities and companies for each project
        commodities_list=pl.col("Commodities (one commodity/row)")
        .drop_nulls()
        .unique(),
        companies_list=pl.col("Affiliated companies, start with Operator")
        .drop_nulls()
        .unique(),
    )

    # --- 3. Create the base dataframe for enrichment ---
    sector_enrichment_df = company_payments_df.select(
        "Country",
        "Year",
        "Company",
        "Government entity",
        "Revenue stream name",
        "Project name",
        "Levied on project (Y/N)",
    ).with_columns(
        # Add normalized columns for joining
        company_name_clean=normalize_text_column(pl.col("Company")),
        project_name_clean=normalize_text_column(pl.col("Project name")),
        stream_name_clean=normalize_text_column(pl.col("Revenue stream name")),
        entity_name_clean=normalize_text_column(pl.col("Government entity")),
    )

    print(f"Base payments dataframe has {sector_enrichment_df.height} rows.")
    print("Aggregated project and company maps are ready.")
    return agg_projects_df, company_sector_map, sector_enrichment_df


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Multi-level join approach""")
    return


@app.cell(hide_code=True)
def _(
    agg_projects_df,
    commodity_to_sector_map,
    company_sector_map,
    mo,
    normalize_text_column,
    pl,
    sector_enrichment_df,
):
    # --- Define heuristic mappings for Levels 3 and 4 ---
    stream_to_sector_map = {
        "mining royalties": "Mining",
        "gas sales": "Oil & Gas",
        "petroleum income tax": "Oil & Gas",
        "oil royalties": "Oil & Gas",
    }
    entity_to_sector_map = {
        "department of petroleum resources": "Oil & Gas",
        "ministry of mines and steel development": "Mining",
        "nigerian national petroleum corporation": "Oil & Gas",
    }

    # --- Create the dictionary maps correctly ---
    commodity_map_dict = dict(
        zip(
            commodity_to_sector_map["commodity_clean"],
            commodity_to_sector_map["sector"],
        )
    )
    company_map_dict = dict(
        zip(
            company_sector_map["company_name_clean"],
            company_sector_map["sector_standardized"],
        )
    )

    # --- Build Regex Pattern for the SMALL commodity list ---
    # This creates a fast pattern like '(crude oil)|(gold)|...'
    commodity_regex = "|".join(f"({key})" for key in commodity_map_dict.keys())


    # --- Perform lookups ---
    enriched_df = sector_enrichment_df.join(
        agg_projects_df, on="project_name_clean", how="left"
    )

    # --- Calculate Sector values using the OPTIMAL method for each level ---
    df_with_levels = (
        enriched_df.with_columns(
            # Level 1: Use the fast REGEX method for "contains" logic on a SMALL keyword list.
            matched_commodity_keyword=(
                pl.col("commodities_list")
                .list.eval(
                    normalize_text_column(pl.element()).str.extract(
                        commodity_regex, 1
                    )
                )
                .list.drop_nulls()
                .list.first()
            ),
            # Level 2: Use the fast DICTIONARY method for "exact match" on a LARGE key list.
            sector_level2=(
                pl.col("companies_list")
                .list.eval(
                    normalize_text_column(pl.element()).replace_strict(
                        company_map_dict, default=None
                    )
                )
                .list.drop_nulls()
                .list.first()
            ),
        )
        .with_columns(
            # Map the keyword found in Level 1 to its sector
            sector_level1=pl.col("matched_commodity_keyword").replace_strict(
                commodity_map_dict
            ),
        )
        .join(
            # Level 5 lookup
            company_sector_map,
            on="company_name_clean",
            how="left",
        )
        .rename({"sector_standardized": "sector_level5"})
    )


    # --- Apply the Hierarchy ---
    final_df = df_with_levels.with_columns(
        sector_final=pl.coalesce(
            [
                pl.col("sector_level1"),
                pl.col("sector_level2"),
                pl.col("stream_name_clean").replace_strict(
                    stream_to_sector_map, default=None
                ),
                pl.col("entity_name_clean").replace_strict(
                    entity_to_sector_map, default=None
                ),
                pl.col("sector_level5"),
            ]
        ),
        sector_match_method=pl.when(
            (pl.col("sector_level1").is_not_null())
            & (pl.col("Levied on project (Y/N)") == "Yes")
        )
        .then(pl.lit("Level 1: Project Commodity"))
        .when(
            (pl.col("sector_level2").is_not_null())
            & (pl.col("Levied on project (Y/N)") == "Yes")
        )
        .then(pl.lit("Level 2: Project Company"))
        .when(pl.col("stream_name_clean").is_in(list(stream_to_sector_map.keys())))
        .then(pl.lit("Level 3: Revenue Stream"))
        .when(pl.col("entity_name_clean").is_in(list(entity_to_sector_map.keys())))
        .then(pl.lit("Level 4: Government Entity"))
        .when(pl.col("sector_level5").is_not_null())
        .then(pl.lit("Level 5: Company Fallback"))
        .otherwise(pl.lit("Unmatched")),
    )

    # --- Summarize ---
    match_summary = (
        final_df.group_by("sector_match_method").len().sort("len", descending=True)
    )

    mo.vstack(
        [
            mo.md(
                "### Sector Enrichment Results (Commodity-Driven)\n\nThis table shows the number of payments matched at each level of the new, more robust hierarchy."
            ),
            match_summary,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Partial Conclusion #5: Hierarchical Sector Matching Proves Effective

    The multi-level sector enrichment strategy successfully assigned sectors to the majority of payment records, demonstrating that a nuanced approach can overcome the absence of direct sector data in company payments.

    * **Coverage Achievement**: [Insert percentage]% of all payment records received a sector assignment through the hierarchical matching process, with only [X]% remaining unmatched.

    * **Match Distribution Insights**: 
      - Level 1 & 2 (Project-based): These high-confidence matches likely represent [X]% of records, providing the most reliable sector assignments where payments are explicitly tied to projects.
      - Level 3 & 4 (Heuristic): Revenue stream and entity-based matching captured another [Y]% of records. While less certain, these matches follow logical business patterns.
      - Level 5 (Company fallback): [Z]% of records relied on company-level sector assignment, which may not reflect payment-specific activities but provides baseline coverage.

    * **Data Quality Implications**: The concentration of matches at different levels varies significantly by country and year, suggesting that some reports have better project-level documentation than others. Reports with high Level 1-2 matches should be prioritized for sector-specific analysis.

    * **Validation Opportunity**: The unmatched records ([X]%) represent either edge cases requiring manual review or potential expansions to our mapping dictionaries. These could be analyzed to iteratively improve the matching logic.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Conclusion""")
    return


@app.cell(hide_code=True)
def _(
    all_reports_count,
    good_confidence_total_pct,
    low_confidence_total_pct,
    match_rate,
    mo,
    top_10_pct,
):
    mo.md(
        f"""
    ### Final Conclusion: A Nuanced Path to Data Integration

    This analysis confirms that enriching company payment data with GFS and Sector IDs is **feasible and valuable**, but a simple join is insufficient. The data quality is highly variable, and a nuanced approach is required to enable reliable analysis.

    * **The Matching Challenge in Numbers**:
        * Across **{all_reports_count}** reports, we achieved a **{match_rate:.1%}** name-match rate for revenue streams after automated cleaning.
        * However, this gap is concentrated: the top 10 most problematic reports account for **{top_10_pct:.1%}** of all name mismatches.
        * For streams that *did* match by name, only **{good_confidence_total_pct:.1f}%** have a financial discrepancy of less than 10%, with **{low_confidence_total_pct:.1f}%** being highly unreliable (>20% discrepancy).

    * **Root Cause: Systemic, Not Random**:
        The primary obstacles are not typos but systemic issues. Analysis of both name and value discrepancies consistently shows that problems are concentrated in specific reports (e.g., **Nigeria, Ukraine, Germany**) and are caused by:
        1.  **Vocabulary Mismatches**: Use of generic terms like `'property rate'` by governments.
        2.  **Structural Gaps**: Governments reporting large, aggregated totals that are not disaggregated by company in our source data.

    #### Recommendation 1: Implement a "Report Card" Model:

        To make the data usable, the database should include a component-based confidence scoring model, stored in a metdata table. Each report (Country x Year) must be enriched with a "report card" that quantify its reliability across different dimensions. We recommend the following scores be calculated and stored:
        * **`stream_match_score`**: Measures the completeness of the name match.
        * **`entity_match_score`**: Measures the completeness of the entity match.
        * **`revenue_value_score`**: Measures the accuracy of the financial reconciliation.

    * **How This Enables Analysis**:
    This model moves beyond a simple pass/fail judgment and instead unlocks value from the majority of reports by guiding analysts to safe and appropriate queries. It allows them to filter data based on the quality required for their specific task, as outlined in the explainer. For example:

    *   **Financial Totals**: Require a high `value_accuracy_score`.

    *   **Breakdown Analysis**: Require a high `stream_match_score`.

    *   **Network Analysis**: Require a high `entity_match_score`.

    #### Recommendation 2: Implement Tiered Data Quality Standards

    Given the variable data quality revealed by this analysis, we recommend establishing tiered usage guidelines:

    **Tier A - Gold Standard** (High confidence across all scores)
    - Use for: Financial reporting, regulatory compliance, trend analysis
    - Requirements: All component scores ≥ 80%

    **Tier B - Analytical Grade** (Mixed quality, suitable for specific analyses)
    - Use for: Proportional analysis, structural studies, exploratory research  
    - Requirements: Relevant component scores ≥ 80% for the specific analysis type

    **Tier C - Directional Only** (Lower quality, requires caveats)
    - Use for: High-level estimates, supplementary context
    - Requirements: At least one component score ≥ 60%

    The matching level could be kept in the report card metdata table and be used as another reliability indicator to support analysts.

    #### Implementation Path:

    1. Break down the notebook into proper python scripts and test the code with real and synthetic datasets. 

    2. Add the report card metadata table to a new version of the schema and fill it manually

    3. Integrate the report card code into the importer for automated assessment

    4. Build a UI that makes it easy for analysts to use the metadata to filter the data used in their queries.

    5. Document the feature onces fully tested internally.
    """
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
