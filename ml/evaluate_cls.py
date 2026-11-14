"""Evaluate YOLOv8n-cls classifier on the held-out test split.

Outputs metrics.json with precision, recall, F1, confusion matrix, sizes, config, git hash.
Run in the ML environment only (requires ultralytics + PyTorch).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def get_git_hash() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def evaluate(
    model_path: Path,
    test_data_dir: Path,
    out_dir: Path = Path("ml/results/"),
) -> None:
    try:
        from ultralytics import YOLO  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError("ultralytics must be installed in the ml/ environment") from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(model_path))

    # Evaluate on test split
    metrics = model.val(data=str(test_data_dir), split="test")

    # Extract metrics
    top1 = float(getattr(metrics, "top1", 0.0))
    top5 = float(getattr(metrics, "top5", 0.0))
    confusion = getattr(metrics, "confusion_matrix", None)
    cm_matrix = (
        confusion.matrix.tolist()
        if confusion is not None and hasattr(confusion, "matrix")
        else []
    )

    # Compute per-class precision, recall, false alarm rate
    ev_recall = 0.0
    ev_precision = 0.0
    ev_false_alarm = 0.0
    f1 = 0.0

    if len(cm_matrix) >= 2 and len(cm_matrix[0]) >= 2:
        # Assuming class 0 is emergency, class 1 is normal
        # cm[i][j]: actual i, predicted j
        tp = float(cm_matrix[0][0])
        fn = float(cm_matrix[0][1])
        fp = float(cm_matrix[1][0])
        tn = float(cm_matrix[1][1])

        ev_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        ev_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        ev_false_alarm = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        f1 = (
            (2 * ev_precision * ev_recall) / (ev_precision + ev_recall)
            if (ev_precision + ev_recall) > 0
            else 0.0
        )

    results = {
        "git_hash": get_git_hash(),
        "model": str(model_path),
        "test_data": str(test_data_dir),
        "top1_accuracy": top1,
        "top5_accuracy": top5,
        "ev_precision": ev_precision,
        "ev_recall": ev_recall,
        "ev_false_alarm": ev_false_alarm,
        "f1_score": f1,
        "confusion_matrix": cm_matrix,
    }

    metrics_file = out_dir / "metrics.json"
    metrics_file.write_text(json.dumps(results, indent=2))
    print(f"Evaluation complete. Metrics saved to {metrics_file}:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=Path)
    parser.add_argument("test_data_dir", type=Path)
    parser.add_argument("--out_dir", type=Path, default=Path("ml/results/"))
    args = parser.parse_args()
    evaluate(args.model_path, args.test_data_dir, out_dir=args.out_dir)
