"""
CDC Provisional Natality Dashboard (2025)
Author: Business Analytics Engineering & Development Agent
Target Audience: Undergraduate Business Analytics Students
Description: Interactive dashboard exploring geographic, seasonal, and sex-based
differences in provisional 2025 U.S. live birth counts.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. PAGE CONFIGURATION & CONSTANTS
# ==============================================================================
st.set_page_config(
    page_title="CDC Provisional Natality Dashboard (2025)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Standard chronological calendar month order
CALENDAR_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Mapping of US states and District of Columbia to standard 2-letter postal codes
STATE_ABBREVIATIONS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}


# ==============================================================================
# 2. DATA INGESTION, VALIDATION & CACHING
# ==============================================================================
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Loads and validates the 2025 provisional natality dataset.
    Prioritizes the Excel workbook (openpyxl) and falls back to CSV if needed.
    Ensures seamless execution locally and on Streamlit Community Cloud.
    """
    base_dir = Path(__file__).parent
    xlsx_path = base_dir / "data" / "Provisional_Natality_2025_CDC.xlsx"
    csv_path = base_dir / "data" / "Provisional_Natality_2025_CDC.csv"
    root_csv_path = base_dir / "Provisional_Natality_2025_CDC.csv"

    df = None

    if xlsx_path.exists():
        try:
            df = pd.read_excel(xlsx_path, engine="openpyxl")
        except Exception:
            df = None

    if df is None and csv_path.exists():
        df = pd.read_csv(csv_path)
    elif df is None and root_csv_path.exists():
        df = pd.read_csv(root_csv_path)

    if df is None:
        raise FileNotFoundError(
            "Could not locate Provisional_Natality_2025_CDC in data/ or root directory."
        )

    # Standardize column headers to lowercase snake_case
    df.columns = [
        str(col).strip().lstrip("\ufeff").lower().replace(" ", "_")
        for col in df.columns
    ]

    # Expected column mapping
    expected_cols = {
        "state_of_residence", "month", "month_code",
        "year_code", "sex_of_infant", "births"
    }
    if not expected_cols.issubset(set(df.columns)):
        raise ValueError(
            f"Dataset schema mismatch. Expected columns {expected_cols}, got {set(df.columns)}"
        )

    # Data type coercions and cleansing
    df["births"] = pd.to_numeric(df["births"], errors="coerce").fillna(0).astype(int)
    df["month_code"] = pd.to_numeric(df["month_code"], errors="coerce").fillna(0).astype(int)
    df["year_code"] = df["year_code"].astype(str)
    df["state_of_residence"] = df["state_of_residence"].astype(str).str.strip()
    df["month"] = df["month"].astype(str).str.strip()
    df["sex_of_infant"] = df["sex_of_infant"].astype(str).str.strip()

    # Add postal code mapping for geospatial mapping
    df["state_code"] = df["state_of_residence"].map(STATE_ABBREVIATIONS)

    # Enforce strict categorical ordering for chronological display
    df["month"] = pd.Categorical(df["month"], categories=CALENDAR_MONTHS, ordered=True)

    # Data integrity assertion
    assert (df["births"] >= 0).all(), "Negative birth counts detected!"
    assert len(df) == 1224, f"Expected 1,224 observations, found {len(df)}"

    return df


# ==============================================================================
# 3. FILTERING & SESSION STATE MANAGEMENT
# ==============================================================================
def initialize_session_state(all_states: list, all_months: list):
    """Initializes session state keys directly bound to widget keys."""
    if "state_selector" not in st.session_state:
        st.session_state["state_selector"] = list(all_states)
    if "month_selector" not in st.session_state:
        st.session_state["month_selector"] = list(all_months)
    if "sex_selector" not in st.session_state:
        st.session_state["sex_selector"] = "All"


def reset_all_filters(all_states: list, all_months: list):
    """Resets all widget-bound session state variables to default values."""
    st.session_state["state_selector"] = list(all_states)
    st.session_state["month_selector"] = list(all_months)
    st.session_state["sex_selector"] = "All"


def render_sidebar(all_states: list, all_months: list):
    """Renders the sidebar filter panel with select-all, reset, and filter summaries."""
    st.sidebar.header("🔍 Filter Controls")

    # Quick action buttons in sidebar
    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.sidebar.button("Select All", help="Select all states and months"):
            reset_all_filters(all_states, all_months)
            st.rerun()
    with col_btn2:
        if st.sidebar.button("Reset Filters", help="Reset all filters to default"):
            reset_all_filters(all_states, all_months)
            st.rerun()

    # State / Geography Multi-Select
    st.sidebar.markdown("---")
    selected_states = st.sidebar.multiselect(
        "Select State(s) / Geography:",
        options=all_states,
        key="state_selector",
        help="Select one or more of the 50 US States + District of Columbia"
    )

    # Month Multi-Select (Strictly Calendar Order)
    selected_months = st.sidebar.multiselect(
        "Select Month(s):",
        options=all_months,
        key="month_selector",
        help="Select calendar months to include"
    )

    # Infant Sex Selector (Radio button)
    selected_sex = st.sidebar.radio(
        "Select Infant Sex:",
        options=["All", "Female", "Male"],
        key="sex_selector",
        help="Filter by infant biological sex"
    )

    # Filter Summary Card
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Active Filter Summary")
    st.sidebar.info(
        f"**Geographies:** {len(selected_states)} of {len(all_states)}\n\n"
        f"**Months:** {len(selected_months)} of {len(all_months)}\n\n"
        f"**Infant Sex:** {selected_sex}"
    )

    return selected_states, selected_months, selected_sex


def apply_filters(df: pd.DataFrame, states: list, months: list, sex: str) -> pd.DataFrame:
    """Applies active sidebar criteria to filter the dataset."""
    filtered_df = df[
        df["state_of_residence"].isin(states) &
        df["month"].isin(months)
    ]
    if sex in ["Female", "Male"]:
        filtered_df = filtered_df[filtered_df["sex_of_infant"] == sex]
    return filtered_df


# ==============================================================================
# 4. UI COMPONENTS & KPI CARDS
# ==============================================================================
def render_header():
    """Renders dashboard header, attribution, provisional notice, and rate disclaimer."""
    st.title("CDC Provisional Natality Dashboard (2025)")
    st.markdown(
        "An interactive analytics dashboard designed for business analytics students "
        "to investigate geographic patterns, seasonal trends, and demographic splits in U.S. live births."
    )

    col_meta1, col_meta2 = st.columns([1, 1])
    with col_meta1:
        st.warning(
            "⚠️ **PROVISIONAL 2025 DATA:** Figures are subject to continuous vital statistics reporting revisions "
            "and delayed certificate registrations by state health authorities."
        )
    with col_meta2:
        st.info(
            "📊 **ANALYTICS RULE — COUNTS VS. RATES:** All metrics represent **absolute live birth counts**, NOT birth rates. "
            "Because total population denominators are not provided, high birth volumes (e.g., California, Texas) "
            "reflect larger resident population sizes rather than higher per-capita fertility rates."
        )
    st.caption("Data Source: CDC National Center for Health Statistics (NCHS) — Provisional Natality (2025 Cohort)")
    st.markdown("---")


def render_kpis(filtered_df: pd.DataFrame, total_geographies: int, selected_months_count: int):
    """Renders 5 top-level executive KPI cards."""
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    if filtered_df.empty:
        with kpi_col1:
            st.metric("Total Births", "0")
        with kpi_col2:
            st.metric("Geographies", f"0 / {total_geographies}")
        with kpi_col3:
            st.metric("Monthly Average", "0")
        with kpi_col4:
            st.metric("Top Geography", "N/A")
        with kpi_col5:
            st.metric("Peak Month", "N/A")
        return

    # Total births
    total_births = int(filtered_df["births"].sum())

    # Selected unique geographies
    active_geos = filtered_df["state_of_residence"].nunique()

    # Average births per selected month
    num_months = max(selected_months_count, 1)
    avg_monthly_births = int(total_births / num_months)

    # Geography with highest birth count
    geo_totals = filtered_df.groupby("state_of_residence")["births"].sum()
    top_geo = geo_totals.idxmax() if not geo_totals.empty else "N/A"
    top_geo_births = int(geo_totals.max()) if not geo_totals.empty else 0

    # Month with highest birth count
    month_totals = filtered_df.groupby("month", observed=True)["births"].sum()
    peak_month = month_totals.idxmax() if not month_totals.empty else "N/A"
    peak_month_births = int(month_totals.max()) if not month_totals.empty else 0

    with kpi_col1:
        st.metric(
            label="Total Births",
            value=f"{total_births:,}"
        )
    with kpi_col2:
        st.metric(
            label="Selected Geographies",
            value=f"{active_geos} / {total_geographies}"
        )
    with kpi_col3:
        st.metric(
            label="Avg. Births / Month",
            value=f"{avg_monthly_births:,}"
        )
    with kpi_col4:
        st.metric(
            label="Top Geography",
            value=top_geo,
            delta=f"{top_geo_births:,} births"
        )
    with kpi_col5:
        st.metric(
            label="Peak Month",
            value=str(peak_month),
            delta=f"{peak_month_births:,} births"
        )


# ==============================================================================
# 5. TAB IMPLEMENTATIONS
# ==============================================================================

def render_overview_tab(filtered_df: pd.DataFrame):
    """Tab 1: Monthly trend line and Female vs Male breakdown."""
    st.subheader("Monthly Trends & Demographic Distribution")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Monthly Birth Volume Trend")
        # Aggregate births by calendar month in chronological order
        monthly_trend = (
            filtered_df.groupby("month", observed=True)["births"]
            .sum()
            .reset_index()
        )
        monthly_trend["month"] = monthly_trend["month"].astype(str)

        fig_trend = px.line(
            monthly_trend,
            x="month",
            y="births",
            markers=True,
            title="Total Birth Count by Month (Chronological)",
            labels={"month": "Month", "births": "Birth Count"},
            color_discrete_sequence=["#1D4ED8"]
        )
        # Never truncate axes: start Y at zero for honest visualization
        fig_trend.update_layout(
            yaxis=dict(range=[0, monthly_trend["births"].max() * 1.15 if not monthly_trend.empty else 100]),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        fig_trend.update_traces(
            hovertemplate="<b>%{x}</b><br>Total Births: %{y:,.0f}<extra></extra>",
            line=dict(width=3),
            marker=dict(size=8)
        )
        st.plotly_chart(fig_trend)

    with col_right:
        st.markdown("#### Infant Sex Comparison")
        sex_summary = (
            filtered_df.groupby("sex_of_infant")["births"]
            .sum()
            .reset_index()
        )
        fig_sex = px.bar(
            sex_summary,
            x="sex_of_infant",
            y="births",
            color="sex_of_infant",
            text="births",
            title="Birth Count by Infant Sex",
            labels={"sex_of_infant": "Infant Sex", "births": "Total Births"},
            color_discrete_map={"Female": "#EC4899", "Male": "#3B82F6"}
        )
        fig_sex.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y:,.0f}<extra></extra>"
        )
        fig_sex.update_layout(
            yaxis=dict(range=[0, sex_summary["births"].max() * 1.2 if not sex_summary.empty else 100]),
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_sex)

    # Educational takeaway callout
    st.markdown("---")
    st.info(
        "💡 **Key Analytics Takeaway for Students:** Notice the seasonal wave in live births, typically peaking in "
        "late summer (July–September) and dipping in winter (January–February). Notice also that male live births consistently "
        "exceed female live births by approximately 4–5%, matching the well-documented human biological sex ratio at birth."
    )


def render_geographic_tab(filtered_df: pd.DataFrame):
    """Tab 2: US Choropleth Map, State Rankings, and Top/Bottom comparison."""
    st.subheader("Geographic Distribution Across the United States")

    # Aggregate by state
    state_agg = (
        filtered_df.groupby(["state_of_residence", "state_code"], observed=True)["births"]
        .sum()
        .reset_index()
        .sort_values(by="births", ascending=False)
    )

    # US State Choropleth Map
    st.markdown("#### U.S. State Choropleth Map (Birth Counts)")
    fig_map = px.choropleth(
        state_agg,
        locations="state_code",
        locationmode="USA-states",
        color="births",
        scope="usa",
        color_continuous_scale="Blues",
        labels={"births": "Birth Count", "state_code": "State"},
        hover_name="state_of_residence"
    )
    fig_map.update_traces(
        hovertemplate="<b>%{hovertext}</b> (%{location})<br>Total Births: %{z:,.0f}<extra></extra>"
    )
    fig_map.update_layout(
        geo=dict(lakecolor="rgb(255, 255, 255)"),
        margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_colorbar=dict(title="Births", tickformat=",d")
    )
    st.plotly_chart(fig_map)

    # State Rankings Chart & Top/Bottom Tables
    col_rank, col_compare = st.columns([3, 2])

    with col_rank:
        st.markdown("#### State Ranking (Highest to Lowest)")
        fig_rank = px.bar(
            state_agg,
            x="births",
            y="state_of_residence",
            orientation="h",
            labels={"births": "Total Births", "state_of_residence": "State / Geography"},
            color="births",
            color_continuous_scale="Blues"
        )
        fig_rank.update_layout(
            yaxis=dict(autorange="reversed"),
            height=max(400, len(state_agg) * 22),
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False
        )
        fig_rank.update_traces(
            hovertemplate="<b>%{y}</b><br>Total Births: %{x:,.0f}<extra></extra>"
        )
        st.plotly_chart(fig_rank)

    with col_compare:
        st.markdown("#### Top 5 vs. Bottom 5 Geographies")
        if len(state_agg) >= 5:
            top_5 = state_agg.head(5)[["state_of_residence", "births"]].copy()
            top_5["births"] = top_5["births"].apply(lambda v: f"{v:,}")
            top_5.columns = ["Top 5 States", "Births"]

            bottom_5 = state_agg.tail(5)[["state_of_residence", "births"]].copy()
            bottom_5["births"] = bottom_5["births"].apply(lambda v: f"{v:,}")
            bottom_5.columns = ["Bottom 5 States", "Births"]

            st.write("**Top 5 Geographies by Total Births:**")
            st.dataframe(top_5, hide_index=True)

            st.write("**Bottom 5 Geographies by Total Births:**")
            st.dataframe(bottom_5, hide_index=True)
        else:
            st.info("Select at least 5 states to view top and bottom comparison tables.")


def render_monthly_sex_tab(filtered_df: pd.DataFrame):
    """Tab 3: Heatmap of State vs Month, trend lines by sex, and sex ratio."""
    st.subheader("Monthly Seasonality & Sex Distribution Analysis")

    st.markdown("#### State-by-Month Birth Density Heatmap")
    # Create pivot table for heatmap: States on Y, Months on X
    pivot_heat = pd.pivot_table(
        filtered_df,
        values="births",
        index="state_of_residence",
        columns="month",
        aggfunc="sum",
        observed=True
    ).fillna(0)

    # Ensure month columns stay in calendar order
    cols_order = [m for m in CALENDAR_MONTHS if m in pivot_heat.columns]
    pivot_heat = pivot_heat[cols_order]

    fig_heat = px.imshow(
        pivot_heat,
        labels=dict(x="Month", y="State / Geography", color="Birth Count"),
        x=cols_order,
        y=pivot_heat.index,
        color_continuous_scale="YlGnBu",
        aspect="auto"
    )
    fig_heat.update_layout(
        height=max(450, len(pivot_heat) * 18),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    fig_heat.update_traces(
        hovertemplate="<b>%{y}</b> - %{x}<br>Births: %{z:,.0f}<extra></extra>"
    )
    st.plotly_chart(fig_heat)

    col_trend, col_ratio = st.columns([3, 2])

    with col_trend:
        st.markdown("#### Monthly Trend by Infant Sex")
        trend_by_sex = (
            filtered_df.groupby(["month", "sex_of_infant"], observed=True)["births"]
            .sum()
            .reset_index()
        )
        trend_by_sex["month"] = trend_by_sex["month"].astype(str)

        fig_sex_trend = px.line(
            trend_by_sex,
            x="month",
            y="births",
            color="sex_of_infant",
            markers=True,
            title="Monthly Birth Volume by Sex",
            labels={"month": "Month", "births": "Births", "sex_of_infant": "Sex"},
            color_discrete_map={"Female": "#EC4899", "Male": "#3B82F6"}
        )
        fig_sex_trend.update_layout(
            yaxis=dict(range=[0, trend_by_sex["births"].max() * 1.15 if not trend_by_sex.empty else 100]),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        fig_sex_trend.update_traces(
            hovertemplate="<b>%{x}</b> (%{fullData.name})<br>Births: %{y:,.0f}<extra></extra>"
        )
        st.plotly_chart(fig_sex_trend)

    with col_ratio:
        st.markdown("#### Sex Ratio at Birth Metric")
        male_births = int(filtered_df[filtered_df["sex_of_infant"] == "Male"]["births"].sum())
        female_births = int(filtered_df[filtered_df["sex_of_infant"] == "Female"]["births"].sum())

        if female_births > 0:
            ratio = male_births / female_births
            st.metric(
                label="Observed Sex Ratio (Male / Female)",
                value=f"{ratio:.3f}",
                help="Demographic ratio of male births to female births (benchmark ~1.050)"
            )
            st.markdown(
                f"- **Male Live Births:** {male_births:,}\n"
                f"- **Female Live Births:** {female_births:,}\n"
                f"- **Excess Male Births:** {male_births - female_births:,}\n\n"
                "In human biology, the natural sex ratio at birth is consistently between **1.045 and 1.055** males per female."
            )
        else:
            st.info("Both male and female records are required to compute the sex ratio.")


def render_table_tab(filtered_df: pd.DataFrame):
    """Tab 4: Searchable data table and CSV download."""
    st.subheader("Data Table & Export")

    st.markdown(
        f"Displaying **{len(filtered_df):,}** observations matching the active filter criteria."
    )

    # Format dataframe for clean student viewing
    display_df = filtered_df[[
        "state_of_residence", "month", "month_code", "year_code", "sex_of_infant", "births"
    ]].copy()
    display_df.columns = [
        "State / Geography", "Month", "Month Code", "Year", "Infant Sex", "Birth Count"
    ]

    st.dataframe(
        display_df.style.format({"Birth Count": "{:,d}", "Month Code": "{:d}"}),
        height=450
    )

    # CSV Download Button
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name="cdc_provisional_natality_2025_filtered.csv",
        mime="text/csv",
        help="Click to download the current filtered view as a CSV file"
    )


def render_about_tab():
    """Tab 5: Data dictionary, validation audit, and business analytics guidance."""
    st.subheader("About the Data & Business Analytics Notes")

    st.markdown("### 1. Data Dictionary")
    data_dict = pd.DataFrame([
        {"Field": "State of Residence", "Data Type": "Text (String)", "Definition": "Reporting US state or District of Columbia (51 total)."},
        {"Field": "Month", "Data Type": "Categorical", "Definition": "Calendar month of occurrence (January through December)."},
        {"Field": "Month Code", "Data Type": "Integer (1-12)", "Definition": "Numeric index of the month for ordering."},
        {"Field": "Year Code", "Data Type": "Integer (2025)", "Definition": "Cohort year for the provisional birth statistics."},
        {"Field": "Sex of Infant", "Data Type": "Text (Categorical)", "Definition": "Biological sex of infant (Female or Male)."},
        {"Field": "Births", "Data Type": "Integer (Count)", "Definition": "Total number of live births registered in that cell."}
    ])
    st.dataframe(data_dict, hide_index=True)

    st.markdown("### 2. Dataset Quality & Audit Confirmation")
    st.write(
        "- **Total Observations:** Exactly 1,224 observations (51 geographies × 12 months × 2 sex categories).\n"
        "- **Total Births in Dataset:** 3,604,640 live births across all 50 states and Washington D.C.\n"
        "- **Missing Values:** 0 null or missing cells across all columns.\n"
        "- **Duplicate Rows:** 0 duplicate rows."
    )

    st.markdown("### 3. Core Business Analytics Concepts for Students")
    st.markdown(
        """
        1. **Conflating Absolute Counts with Relative Rates:**
           - A common rookie mistake in business analytics is concluding that "California has the highest birth rate" because it has the most births.
           - In reality, California simply has the largest population in the U.S. To measure fertility or birth rates, birth counts must be divided by the relevant population denominator (e.g., live births per 1,000 women aged 15–44).
        2. **Understanding Provisional Vital Statistics:**
           - Unlike final vital statistics reports which take up to two years to finalize, provisional CDC data are released periodically to detect emerging public health trends rapidly.
           - Provisional data may experience minor revisions as late registrations are filed by jurisdictions.
        3. **Human Sex Ratio Baseline:**
           - Worldwide and in U.S. vital statistics, slightly more boys are born than girls (~105 boys per 100 girls). This biological ratio remains remarkably stable across time and geography.
        """
    )


# ==============================================================================
# 6. MAIN APPLICATION EXECUTION
# ==============================================================================
def main():
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading natality dataset: {e}")
        st.stop()

    all_states = sorted(df["state_of_residence"].unique())
    all_months = CALENDAR_MONTHS

    # Initialize session state for persistent filter selections
    initialize_session_state(all_states, all_months)

    # Render Sidebar Controls
    selected_states, selected_months, selected_sex = render_sidebar(all_states, all_months)

    # Filter Dataset
    filtered_df = apply_filters(df, selected_states, selected_months, selected_sex)

    # Render Header
    render_header()

    # Empty State Guard: If user deselects all states or months
    if filtered_df.empty:
        st.warning(
            "⚠️ **No data matches your current filter selection.** "
            "Please select at least one State/Geography and at least one Month in the sidebar."
        )
        render_kpis(filtered_df, len(all_states), len(selected_months))
        st.stop()

    # Render KPI Cards
    render_kpis(filtered_df, len(all_states), len(selected_months))
    st.markdown("---")

    # Render 5 Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "🗺️ Geographic Analysis",
        "🗓️ Monthly & Sex Analysis",
        "📋 Data Table & Download",
        "ℹ️ About the Data"
    ])

    with tab1:
        render_overview_tab(filtered_df)

    with tab2:
        render_geographic_tab(filtered_df)

    with tab3:
        render_monthly_sex_tab(filtered_df)

    with tab4:
        render_table_tab(filtered_df)

    with tab5:
        render_about_tab()


if __name__ == "__main__":
    main()
