#!/bin/bash
# DO NOT hardcode bucket, export MLFLOW_ARTIFACTS_DESTINATION before running this if needed,
# or default to the placeholder (ensure you replace it in terminal).
export MLFLOW_ARTIFACTS_DESTINATION=${MLFLOW_ARTIFACTS_DESTINATION:-"gs://oppe2-artifacts-42aa52a6"}

mkdir -p ~/oppe2_workspace/mlflow
nohup mlflow server \
  --backend-store-uri sqlite:////home/$USER/oppe2_workspace/mlflow/mlflow.db \
  --artifacts-destination "$MLFLOW_ARTIFACTS_DESTINATION" \
  --host 0.0.0.0 \
  --port 8100 \
  > ~/oppe2_workspace/mlflow/mlflow.log 2>&1 &
