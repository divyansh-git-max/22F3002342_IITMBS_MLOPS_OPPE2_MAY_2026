# AI-Assisted Development Record

This is a curated record of the major development questions and the guidance provided. It captures the engineering process, not a word-for-word transcript of private chats.

## Environment and terminal decisions

**Student:** Which service, VM, and terminal should I use?

**Guidance:**

- Use local VS Code / PowerShell to edit files and commit/push Git changes.
- Use Google Cloud Shell to create and inspect GCP resources and observe Kubernetes with kubectl.
- Use the development VM over SSH to train, run MLflow, send the 100 requests, and run wrk.
- Use GCP Console for Cloud Logging evidence and GitHub Actions for CI/CD.

**Decision:** Use OPPE-specific resources in project project-42aa52a6-0cc6-4d7b-863: VM instance-20260905-173452, bucket gs://oppe2-artifacts-42aa52a6, Artifact Registry oppe2-repo, and GKE oppe2-cluster.

## Deliverables

**Student:** Every deliverable must be complete. What proof is needed?

**Guidance:** Provide SHAP analysis for explainability, Fairlearn metrics using age, Docker/GKE/GitHub Actions for deployment, an HPA capped at three pods, structured API logs in Cloud Logging, 100 recorded per-sample requests, a wrk result above 2,000 connections, and an Evidently comparison of training data with the exact sample sent to the API.

## MLflow

**Student:** Which MLflow URI and artifacts should be used?

**Guidance:** Do not reuse older unrelated models or buckets. Run MLflow on the OPPE VM with VM-local SQLite metadata and the new OPPE GCS bucket as the artifact store. Before training, set MLFLOW_TRACKING_URI=http://127.0.0.1:8100.

**Reasoning:** Cloud Shell is temporary. The VM provides persistent local metadata and prepared compute; GCS keeps artifacts independent of the boot disk.

## GKE deployment failure

**Student:** Why did GitHub Actions fail at kubectl apply?

**Observed error:** gke-gcloud-auth-plugin not found.

**Diagnosis:** Google Cloud authentication worked, but kubectl on the GitHub-hosted runner lacked the GKE credential plugin needed to access the cluster API.

**Fix applied:** The CD workflow now uses google-github-actions/setup-gcloud@v2 with install_components: gke-gcloud-auth-plugin and verifies the plugin before obtaining credentials. This fixes authentication instead of bypassing validation with --validate=false.

## Prediction-sample correction

**Student:** What should run after the workflow succeeds?

**Guidance:** Verify rollout and /health, obtain the LoadBalancer IP, send the 100 rows from the VM, inspect Cloud Logging, run wrk, and watch the HPA in Cloud Shell.

**Issue found:** The request client treated gender as numeric although the CSV already contains male/female strings. This changed every sent row to male, breaking the requirement that deployed requests match the drift-reference sample.

**Fix applied:** The unnecessary conversion was removed, so the original sampled rows are sent to the API.

## Concepts

**Student:** What are pods, kubectl, HPA, wrk, and predict.lua?

**Guidance:** A pod is the smallest deployable Kubernetes unit; here it runs one FastAPI container. kubectl manages and inspects the cluster. The HPA changes the API from one to at most three pods based on CPU. wrk is a HTTP benchmark tool that reveals throughput, latency, and timeout behaviour under concurrent load. predict.lua gives wrk a valid JSON body for POST /predict.

```bash
wrk -t4 -c2200 -d60s --timeout 10s -s loadtest/predict.lua "http://EXTERNAL_IP/predict"
```

## Final evidence checklist

1. Repository privacy and accepted collaborator access.
2. SHAP least-impact explanation and figure.
3. Fairlearn age-based metrics and conclusion.
4. Successful GitHub Actions CI/CD run.
5. GKE pods, LoadBalancer, HPA configuration, and scale-up proof.
6. Successful API prediction and Cloud Logging entries.
7. 100-request output and prediction_results.csv.
8. wrk throughput, latency, and timeout/error output.
9. Evidently drift report and summary.

## Cleanup

**Student:** What should remain running after the work is complete?

**Guidance:** Keep resources running only until evidence is captured. Then stop the VM and delete the GKE cluster when no longer needed to avoid continuing compute and LoadBalancer charges.
