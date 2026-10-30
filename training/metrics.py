import json
from pathlib import Path
import numpy as np

def classification_metrics(y_true, y_pred, class_names=None):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    n = len(class_names) if class_names else int(max(y_true.max(initial=0), y_pred.max(initial=0)) + 1)
    cm = np.zeros((n,n), dtype=int)
    for a,b in zip(y_true,y_pred): cm[a,b] += 1
    tp=np.diag(cm); precision=tp/np.maximum(cm.sum(0),1); recall=tp/np.maximum(cm.sum(1),1); f1=2*precision*recall/np.maximum(precision+recall,1e-12)
    return {"accuracy": float(tp.sum()/max(len(y_true),1)), "precision": float(precision.mean()), "recall": float(recall.mean()), "f1": float(f1.mean()), "per_class_accuracy": (tp/np.maximum(cm.sum(1),1)).tolist(), "confusion_matrix": cm.tolist()}

def save_metrics(metrics, path="reports/training_results.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True); Path(path).write_text(json.dumps(metrics, indent=2))
