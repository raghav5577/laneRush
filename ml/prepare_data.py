"""Prepare detection dataset — deduplicate, fixed-seed 70/15/15 split."""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path


def prepare(
    raw_dir: Path,
    out_dir: Path,
    seed: int = 42,
    train: float = 0.70,
    val: float = 0.15,
) -> None:
    """Split images into train/val/test sets.

    Inspect the dataset first: if it has boxes (YOLO format .txt labels),
    use two-stage design (COCO YOLO boxes → crop → classifier).
    If classification-only, copy directly.
    """
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect all images
    images = sorted(raw_dir.glob("**/*.jpg")) + sorted(raw_dir.glob("**/*.png"))
    # Deduplicate by filename stem
    seen: set[str] = set()
    unique: list[Path] = []
    for img in images:
        if img.stem not in seen:
            seen.add(img.stem)
            unique.append(img)

    rng.shuffle(unique)
    n = len(unique)
    n_train = int(n * train)
    n_val = int(n * val)
    splits = {
        "train": unique[:n_train],
        "val": unique[n_train: n_train + n_val],
        "test": unique[n_train + n_val:],
    }

    for split_name, files in splits.items():
        split_dir = out_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(f, split_dir / f.name)

    meta = {
        "seed": seed,
        "total": n,
        "train": len(splits["train"]),
        "val": len(splits["val"]),
        "test": len(splits["test"]),
    }
    (out_dir / "split_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Split: {meta}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    prepare(args.raw_dir, args.out_dir, seed=args.seed)
