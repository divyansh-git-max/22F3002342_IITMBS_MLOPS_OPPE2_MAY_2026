import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

def main():
    train_df = pd.read_csv('data/data.csv').drop(columns=['sno', 'target'], errors='ignore')
    sample_df = pd.read_csv('data/prediction_sample_100.csv').drop(columns=['target'], errors='ignore')
    
    # ensure schemas match for evidently
    report = Report(metrics=[DataDriftPreset()])
    snapshot = report.run(reference_data=train_df, current_data=sample_df)
    snapshot.save_html('models/drift_report.html')
    
    with open('models/drift_summary.md', 'w') as f:
        f.write("# Data Drift Summary\n")
        f.write("A 100-row sample was generated for predictions.\n")
        f.write("Evidently drift detection was run between the training data and the sample.\n")
        f.write("Results are saved in `models/drift_report.html`.\n")
    print("Drift detection completed. HTML and Markdown summary saved.")

if __name__ == "__main__":
    main()
