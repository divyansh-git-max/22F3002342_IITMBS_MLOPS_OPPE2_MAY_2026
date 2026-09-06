# Heart Disease Prediction — Production MLOps Pipeline

This repository operationalizes a heart disease classifier as an explainable, observable, scalable API on Google Cloud Platform. It was built for the IITM BS MLOps OPPE-2 assessment (Weeks 4–9).

## Objective

The system predicts whether a patient is likely to have heart disease from clinical features. It demonstrates the path from reproducible training to a containerized production API, with explainability, fairness testing, logging, autoscaling, load testing, and input-drift detection.

## Pipeline

```text
Training CSV -> Optuna training + MLflow -> best_model.pkl
                    |-> SHAP feature-impact analysis
                    |-> Fairlearn age-group fairness analysis
                    v
FastAPI /predict -> JSON stdout logs -> GCP Cloud Logging
                    v
Docker -> Artifact Registry -> GitHub Actions (WIF) -> GKE
                    |-> HPA: 1 to 3 pods
                    |-> 100 individual prediction requests
                    |-> wrk stress test and Evidently drift report
```

## Deliverables and evidence

| Requirement | Implementation / evidence |
| --- | --- |
| Explainability | models/shap_summary.png, models/shap_importance.csv, and models/shap_analysis.md |
| Fairness | Age-based Fairlearn results in models/fairness_analysis.md |
| Deployment | Dockerfile, Kubernetes manifests, and GitHub Actions workflows |
| Scaling | k8s/hpa.yaml with maximum three API pods |
| Observability | app/main.py emits timestamped feature and prediction JSON logs |
| Per-sample prediction | data/prediction_sample_100.csv and data/prediction_results.csv |
| Stress testing | loadtest/predict.lua plus captured wrk metrics |
| Drift detection | models/drift_report.html and models/drift_summary.md |

## Repository layout

```text
app/                 FastAPI application and request schema
data/                Source CSV and generated prediction sample
k8s/                 Deployment, LoadBalancer service, and HPA
loadtest/            wrk Lua request payload
models/              Model plus SHAP, fairness, and drift outputs
scripts/             Training, MLflow, prediction, and monitor tools
tests/               API tests
.github/workflows/   CI and CD workflows
```

## API

- GET /health reports whether the model is ready.
- POST /predict accepts one patient record and returns a binary prediction.

Example request:

```json
{
  "age": 50, "gender": "male", "cp": 1, "trestbps": 120,
  "chol": 200, "fbs": 0, "restecg": 1, "thalach": 150,
  "exang": 0, "oldpeak": 1.0, "slope": 1, "ca": 0, "thal": 2
}
```

## Development

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux VM: source .venv/bin/activate
pip install -r requirements.txt
python scripts/train_and_evaluate.py
python scripts/monitor.py
pytest -q
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For VM-based tracking, set MLFLOW_TRACKING_URI to http://127.0.0.1:8100 before training. MLflow uses VM-local SQLite metadata and the OPPE GCS artifact bucket gs://oppe2-artifacts-42aa52a6.

## Cloud deployment

The deployed environment uses the oppe2-repo Artifact Registry repository, the oppe2-cluster GKE cluster in us-central1-a, and the heart-disease-api Deployment. The public service is heart-disease-service.

A push to main runs CI/CD. GitHub Actions authenticates through Workload Identity Federation, builds and pushes the image, then applies the Deployment, Service, and HPA. No static GCP service-account key is stored in GitHub.

```bash
kubectl get svc heart-disease-service
curl http://EXTERNAL_IP/health
```

## Observability and performance

Run the 100-row client from the development VM:

```bash
python scripts/send_prediction_samples.py --base-url "http://EXTERNAL_IP"
```

Use this Logs Explorer filter:

```text
resource.type="k8s_container"
resource.labels.cluster_name="oppe2-cluster"
jsonPayload.timestamp:*
```

Run the required high-concurrency test from the VM while observing kubectl get hpa -w in Cloud Shell:

```bash
wrk -t4 -c2200 -d60s --timeout 10s -s loadtest/predict.lua "http://EXTERNAL_IP/predict"
```

Record throughput, latency, and socket errors or timeouts. The HPA must never exceed three replicas.

## Key outputs

- models/best_model.pkl — model loaded by the API
- models/shap_analysis.md — least-impact feature explanation
- models/fairness_analysis.md — age-group fairness outcome
- models/drift_report.html — interactive input-drift report
- data/prediction_sample_100.csv — shared prediction and drift sample
- data/prediction_results.csv — results from the deployed API

## AI-assisted development

See [AI_DOC.md](AI_DOC.md) for a transparent, curated record of the major questions, decisions, fixes, and guidance used during development.

## Cost cleanup

After saving all assessment evidence, stop the VM and delete the GKE cluster when no longer needed. Running nodes and a LoadBalancer can incur charges.
