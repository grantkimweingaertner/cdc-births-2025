# CDC Provisional Natality 2025 Dashboard

A business analytics web dashboard built with Streamlit, pandas, and Plotly to analyze provisional 2025 CDC live birth statistics across the United States.

## Project Structure
```text
cdc-births-2025/
├── .streamlit/
│   └── config.toml             # Custom UI theme configuration
├── data/
│   ├── Provisional_Natality_2025_CDC.xlsx   # Source Excel workbook
│   └── Provisional_Natality_2025_CDC.csv    # High-speed CSV dataset
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python package dependencies
├── README.md                   # Project documentation & run guide
└── implementation_plan.md      # Engineering specification artifact
```

## How to Run Locally
1. Ensure Python 3.10+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```
4. The dashboard will automatically open in your default browser at `http://localhost:8501`.

## Key Business Analytics Takeaways for Students
1. **Counts vs. Rates:** Absolute birth counts must not be confused with birth rates. Higher counts in populous states like California or Texas reflect larger baseline populations rather than higher fertility.
2. **Seasonality:** U.S. live births demonstrate consistent seasonal variation, typically peaking in late summer (July through September).
3. **Biological Sex Ratio:** Live births consistently exhibit a natural biological ratio of ~105 male births per 100 female births.
