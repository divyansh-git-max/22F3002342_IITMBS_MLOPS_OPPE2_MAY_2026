import argparse
import pandas as pd
import requests

def run(base_url):
    df = pd.read_csv('data/prediction_sample_100.csv')
    df['gender'] = df['gender'].map({1: 'male', 0: 'female'}).fillna('male')
    success = 0
    results = []
    
    for i, row in df.iterrows():
        payload = row.to_dict()
        try:
            resp = requests.post(f"{base_url}/predict", json=payload, timeout=5)
            resp.raise_for_status()
            success += 1
            results.append({"status": "success", "prediction": resp.json()['prediction']})
        except Exception as e:
            results.append({"status": "error", "error": str(e)})
            
    pd.DataFrame(results).to_csv("data/prediction_results.csv", index=False)
    print(f"Sent 100 requests. Success: {success}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    run(args.base_url)
