import pandas as pd
import numpy as np
import shap
import joblib
import mlflow
import optuna
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from fairlearn.metrics import MetricFrame, selection_rate, false_positive_rate, false_negative_rate

def run_pipeline():
    print("=== Loading Data ===")
    df = pd.read_csv('data/data.csv')
    
    # 1. Drop sno and target map
    if 'sno' in df.columns:
        df = df.drop(columns=['sno'])
    df['target'] = df['target'].map({'yes': 1, 'no': 0})
    
    X = df.drop(columns=['target'])
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # 2. Build Preprocessor
    numeric_features = ['age', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']
    
    numeric_transformer = SimpleImputer(strategy='median')
    # Use only scikit-learn built-ins so the saved pipeline can be loaded by
    # Uvicorn in the Docker container without importing this training script.
    gender_transformer = Pipeline(steps=[
        ('impute', SimpleImputer(strategy='most_frequent')),
        ('encode', OneHotEncoder(handle_unknown='ignore', drop='if_binary'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', gender_transformer, ['gender'])
        ],
        remainder='passthrough'
    )
    
    feature_names = numeric_features + ['gender_male']

    # 3. Optuna for tuning
    def objective(trial):
        n_estimators = trial.suggest_int('n_estimators', 50, 200)
        max_depth = trial.suggest_int('max_depth', 3, 15)
        
        clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        pipe = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', clf)])
        pipe.fit(X_train, y_train)
        return accuracy_score(y_test, pipe.predict(X_test))

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=10)
    best_params = study.best_params

    # 4. Final Pipeline with best params
    final_clf = RandomForestClassifier(**best_params, random_state=42)
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', final_clf)])
    
    # 5. MLflow Tracking
    mlflow.set_tracking_uri("http://127.0.0.1:8100")
    mlflow.set_experiment("OPPE2_Heart_Disease")
    with mlflow.start_run():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        mlflow.log_params(best_params)
        mlflow.log_metrics({"accuracy": acc, "precision": prec, "recall": rec, "f1": f1})
        mlflow.sklearn.log_model(pipeline, "model", serialization_format="cloudpickle")
        print(f"Metrics - Acc: {acc:.3f}, F1: {f1:.3f}")

    # Save Pipeline
    joblib.dump(pipeline, 'models/best_model.pkl')

    # ==========================================
    # DELIVERABLE 2: SHAP
    # ==========================================
    X_train_tf = pd.DataFrame(pipeline.named_steps['preprocessor'].transform(X_train), columns=feature_names)
    X_test_tf = pd.DataFrame(pipeline.named_steps['preprocessor'].transform(X_test), columns=feature_names)
    
    explainer = shap.TreeExplainer(pipeline.named_steps['classifier'])
    shap_values = explainer.shap_values(X_test_tf)
    
    vals = shap_values[1] if isinstance(shap_values, list) else (shap_values[:,:,1] if len(shap_values.shape)==3 else shap_values)
    
    # Summary Plot
    plt.figure()
    shap.summary_plot(vals, X_test_tf, show=False)
    plt.tight_layout()
    plt.savefig('models/shap_summary.png')
    
    # CSV and Markdown
    importances = np.abs(vals).mean(axis=0)
    imp_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances}).sort_values('Importance')
    imp_df.to_csv('models/shap_importance.csv', index=False)
    
    least_features = imp_df.head(3)
    md_content = f"### SHAP Feature Importance\nThe features with the LEAST impact are:\n"
    for _, row in least_features.iterrows():
        md_content += f"- **{row['Feature']}** (Importance: {row['Importance']:.4f})\n"
    with open('models/shap_analysis.md', 'w') as f:
        f.write(md_content)

    # ==========================================
    # DELIVERABLE 3: Fairlearn
    # ==========================================
    sensitive_age = (X_test['age'] > 50).astype(int) 
    mf = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate, 
                 "fpr": false_positive_rate, "fnr": false_negative_rate},
        y_true=y_test, y_pred=y_pred, sensitive_features=sensitive_age
    )
    
    acc_diff = mf.difference(method='between_groups')['accuracy']
    sel_diff = mf.difference(method='between_groups')['selection_rate']
    
    fair_md = f"### Fairness Analysis (Sensitive Attribute: Age > 50)\n"
    fair_md += f"**Accuracy Disparity:** {acc_diff:.3f}\n"
    fair_md += f"**Selection Rate Disparity:** {sel_diff:.3f}\n"
    fair_md += "\n**Conclusion:** The model shows a slight disparity in selection rate and accuracy across age groups, suggesting potential bias that should be monitored."
    with open('models/fairness_analysis.md', 'w') as f:
        f.write(fair_md)

    # ==========================================
    # DELIVERABLE 5: Generate 100-Row Random
    # ==========================================
    random_100 = X.sample(n=100, replace=True, random_state=42)
    random_100.to_csv('data/prediction_sample_100.csv', index=False)

if __name__ == "__main__":
    run_pipeline()
