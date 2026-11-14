"""Prepare emergency vehicle classification dataset for YOLOv8-cls.

Supports:
1. Kaggle format with CSV (train.csv with image_names, emergency_or_not) + images/ folder
2. Subfolder format (raw_dir/emergency/ and raw_dir/normal/ or non-emergency/)

Outputs YOLOv8-cls directory structure:
    out_dir/
      train/
        emergency/
        normal/
      val/
        emergency/
        normal/
      test/
        emergency/
        normal/
      split_meta.json
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
from pathlib import Path


def _collect_csv_format(raw_dir: Path) -> dict[str, list[Path]]:
    """Check for train.csv / labels.csv mapping images to 0/1."""
    csv_candidates = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("images/*.csv"))
    if not csv_candidates:
        return {}

    csv_path = csv_candidates[0]
    classes: dict[str, list[Path]] = {"emergency": [], "normal": []}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Kaggle dataset column names are usually image_names & emergency_or_not
            name_key = next((k for k in row if "name" in k.lower() or "image" in k.lower()), None)
            label_key = next((k for k in row if "emerg" in k.lower() or "label" in k.lower() or "target" in k.lower()), None)

            if not name_key or not label_key:
                continue

            img_name = row[name_key].strip()
            label_val = row[label_key].strip()

            # Find image file
            img_path = None
            for candidate in [raw_dir / img_name, raw_dir / "images" / img_name]:
                if candidate.exists():
                    img_path = candidate
                    break

            if not img_path:
                # Search recursively
                matches = list(raw_dir.glob(f"**/{img_name}"))
                if matches:
                    img_path = matches[0]

            if img_path:
                is_emergency = label_val in {"1", "emergency", "True", "true"}
                cls_name = "emergency" if is_emergency else "normal"
                classes[cls_name].append(img_path)

    return classes if (classes["emergency"] and classes["normal"]) else {}


def _collect_folder_format(raw_dir: Path) -> dict[str, list[Path]]:
    """Collect from class subfolders (emergency / normal or non_emergency)."""
    classes: dict[str, list[Path]] = {"emergency": [], "normal": []}

    for path in raw_dir.iterdir():
        if not path.is_dir():
            continue
        lower_name = path.name.lower()
        if "non" in lower_name or "normal" in lower_name or "ordinary" in lower_name:
            target_cls = "normal"
        elif "emerg" in lower_name or "ev" in lower_name:
            target_cls = "emergency"
        else:
            continue

        imgs = sorted(path.glob("*.jpg")) + sorted(path.glob("*.png")) + sorted(path.glob("*.jpeg"))
        classes[target_cls].extend(imgs)

    return classes if (classes["emergency"] and classes["normal"]) else {}


def prepare(
    raw_dir: Path,
    out_dir: Path,
    seed: int = 42,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> None:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Try CSV format
    classes = _collect_csv_format(raw_dir)
    # 2. Try class folder format
    if not classes:
        classes = _collect_folder_format(raw_dir)

    if not classes:
        raise ValueError(
            f"Could not find valid classes in {raw_dir}. Expected either:\n"
            "  1. A CSV file (e.g. train.csv) with columns image_names and emergency_or_not\n"
            "  2. Subfolders: 'emergency' and 'normal' (or 'non_emergency') containing images."
        )

    # Deduplicate within each class
    for cls_name in ["emergency", "normal"]:
        seen: set[str] = set()
        unique: list[Path] = []
        for img in classes[cls_name]:
            if img.name not in seen:
                seen.add(img.name)
                unique.append(img)
        classes[cls_name] = unique

    print(f"Loaded: {len(classes['emergency'])} emergency images, {len(classes['normal'])} normal images")

    # Split each class independently to preserve class balance (stratified 70/15/15)
    splits: dict[str, dict[str, list[Path]]] = {
        "train": {"emergency": [], "normal": []},
        "val": {"emergency": [], "normal": []},
        "test": {"emergency": [], "normal": []},
    }

    for cls_name in ["emergency", "normal"]:
        imgs = classes[cls_name]
        rng.shuffle(imgs)
        n = len(imgs)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        splits["train"][cls_name] = imgs[:n_train]
        splits["val"][cls_name] = imgs[n_train: n_train + n_val]
        splits["test"][cls_name] = imgs[n_train + n_val:]

    # Copy files into YOLOv8-cls directory structure: out_dir/{train,val,test}/{emergency,normal}/
    meta = {
        "seed": seed,
        "splits": {},
    }

    for split_name in ["train", "val", "test"]:
        split_meta = {}
        for cls_name in ["emergency", "normal"]:
            dest_dir = out_dir / split_name / cls_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            files = splits[split_name][cls_name]
            split_meta[cls_name] = len(files)
            for f in files:
                shutil.copy2(f, dest_dir / f.name)
        meta["splits"][split_name] = split_meta

    meta_file = out_dir / "split_meta.json"
    meta_file.write_text(json.dumps(meta, indent=2))
    print(f"Dataset successfully prepared at {out_dir}:")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Kaggle Emergency Vehicle dataset for YOLOv8-cls")
    parser.add_argument("raw_dir", type=Path, help="Directory containing raw Kaggle dataset (train.csv + images/ or emergency/normal folders)")
    parser.add_argument("--out_dir", type=Path, default=Path("data/ev_cls"), help="Destination directory (default: data/ev_cls)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic split")
    args = parser.parse_args()
    prepare(args.raw_dir, args.out_dir, seed=args.seed)
