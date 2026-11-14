"""Train YOLOv8n-cls classifier on the prepared dataset.

Run in the ML environment only (requires ultralytics + PyTorch).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def train(
    data_dir: Path,
    model_name: str = "yolov8n-cls.pt",
    epochs: int = 50,
    imgsz: int = 224,
    seed: int = 42,
    out_dir: Path = Path("ml/runs/"),
) -> None:
    try:
        from ultralytics import YOLO  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError("ultralytics must be installed in the ml/ environment") from exc

    model = YOLO(model_name)
    results = model.train(
        data=str(data_dir),
        epochs=epochs,
        imgsz=imgsz,
        seed=seed,
        project=str(out_dir),
        name="cls_train",
    )
    print(f"Training complete. Results: {results}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--model", default="yolov8n-cls.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out_dir", type=Path, default=Path("ml/runs/"))
    args = parser.parse_args()
    train(args.data_dir, args.model, args.epochs, seed=args.seed, out_dir=args.out_dir)
