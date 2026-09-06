# OPPE 2 Operations Runbook

This repository contains the complete solution for the Heart Disease Prediction deployment pipeline on Google Cloud Platform. 
It satisfies all requirements for Deliverables 1 through 7, including Model Explainability, Fairness Testing, Dockerized API on GKE, Logging, Stress Testing, and Drift Detection.

## A. Google Cloud Shell — start the development VM
```bash
gcloud compute instances start instance-20260905-173452 \
  --zone us-central1-a \
  --project project-42aa52a6-0cc6-4d7b-863
```

## B. Google Cloud Shell — create a NEW OPPE-only artifact/data bucket
```bash
gcloud storage buckets create gs://oppe2-artifacts-42aa52a6 \
  --project project-42aa52a6-0cc6-4d7b-863 \
  --location us-central1 \
  --uniform-bucket-level-access
```

## C. Google Cloud Shell — create Docker Artifact Registry
```bash
gcloud artifacts repositories create oppe2-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project project-42aa52a6-0cc6-4d7b-863
```

## D. Google Cloud Shell — create the GKE cluster
Wait until the exam prompt provides the required cluster name and zone:
```bash
gcloud container clusters create oppe2-cluster \
  --zone us-central1-a \
  --machine-type e2-medium \
  --num-nodes 1 \
  --project project-42aa52a6-0cc6-4d7b-863
```

## E. Google Cloud Shell — SSH to the prepared development VM
```bash
gcloud compute ssh instance-20260905-173452 \
  --zone us-central1-a \
  --project project-42aa52a6-0cc6-4d7b-863
```

## F. VM SSH — activate environment, configure Docker, and configure kubectl
```bash
cd ~/oppe2_workspace/22F3002342_IITMBS_MLOPS_OPPE2_MAY_2026
source ~/oppe2_workspace/.venv/bin/activate
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
gcloud container clusters get-credentials oppe2-cluster \
  --zone us-central1-a \
  --project project-42aa52a6-0cc6-4d7b-863
kubectl get nodes
```

## G. VM SSH — MLflow server
We run a persistent SQLite MLflow backend with GCP bucket artifact storage. The VM identity must have Storage Object Admin access to the new bucket.

```bash
# Verify/Grant Storage Access
gcloud projects add-iam-policy-binding project-42aa52a6-0cc6-4d7b-863 \
  --member="serviceAccount:<YOUR_COMPUTE_DEFAULT_SA>@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

export MLFLOW_ARTIFACTS_DESTINATION=gs://oppe2-artifacts-42aa52a6
bash scripts/run_mlflow_server.sh
```
Verify health:
```bash
curl http://127.0.0.1:8100/version
```

## H. VM SSH — training, MLflow, and local API
Run the data science pipeline (Deliverables 2, 3, 5, 7):
```bash
python scripts/train_and_evaluate.py
```
*(This generates the SHAP plots, Fairness metrics, the 100-row sample dataset, and logs to MLflow).*

Run tests:
```bash
pytest -q
```
Test API locally:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## I. GitHub Actions / CI-CD
Pushing to the `main` branch automatically triggers CI/CD using WIF GitHub secrets (`CD_GCP_WORKLOAD_IDENTITY_PROVIDER` and `CD_GCP_SERVICE_ACCOUNT_EMAIL`).
```bash
git add .
git commit -m "feat: deploying complete pipeline"
git push origin main
```

## J. GKE validation and scaling
After the GitHub Action completes:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl rollout status deployment/heart-disease-api --timeout=300s
kubectl get pods
kubectl get hpa
kubectl get svc heart-disease-service -w
```

## K. Logging and observability
The FastAPI app writes structured JSON logs to stdout. These are automatically collected by GKE Cloud Logging.
1. Go to GCP Console -> **Logging > Logs Explorer**.
2. Run this query:
```text
resource.type="k8s_container"
resource.labels.cluster_name="oppe2-cluster"
resource.labels.container_name="api"
```
3. Use **Cloud Monitoring / Metrics Explorer** to view pod CPU, memory, and HPA autoscaling behavior under load.

## L. 100 prediction requests
Sends the 100 random rows to the deployed GKE load balancer.
```bash
export EXTERNAL_IP=$(kubectl get svc heart-disease-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
python scripts/send_prediction_samples.py --base-url "http://$EXTERNAL_IP:80"
```
Results are saved to `data/prediction_results.csv`.

## M. Stress testing
Simulate >2,000 concurrent users using `wrk` and the Lua payload script:
```bash
wrk -t4 -c2500 -d60s --timeout 10s -s loadtest/predict.lua "http://$EXTERNAL_IP:80/predict"
```
Record requests/sec, latency, and socket errors from the output.
To watch the HPA scale up the pods in real-time, open a second terminal and run:
```bash
watch -n 2 'kubectl get hpa; echo; kubectl get pods -o wide'
```

## N. Drift
After generating the 100-row prediction dataset, run the monitor script:
```bash
python scripts/monitor.py
```
This generates `models/drift_report.html` and `models/drift_summary.md`.

## O. Cleanup — Google Cloud Shell
After taking screenshots and submitting evidence:
```bash
gcloud container clusters delete oppe2-cluster \
  --zone us-central1-a \
  --project project-42aa52a6-0cc6-4d7b-863 \
  --quiet

gcloud compute instances stop instance-20260905-173452 \
  --zone us-central1-a \
  --project project-42aa52a6-0cc6-4d7b-863
```
