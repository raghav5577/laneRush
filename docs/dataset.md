# Emergency Vehicle Detection Dataset Documentation

This document describes the Kaggle Emergency Vehicle Dataset, its structure, format considerations, and the training workflow for **LaneRush**.

---

## 1. Dataset Overview

- **Source:** Kaggle Emergency Vehicle Detection / Classification Dataset
- **Task:** Binary classification — Emergency Vehicle (`1`) vs. Non-Emergency / Ordinary Vehicle (`0`)
- **Key Categories:**
  - **Emergency:** Ambulances, fire engines, police cars.
  - **Normal / Non-Emergency:** Passenger cars, buses, trucks, motorcycles.

---

## 2. Dataset Structure & Inspection

A common pitfall identified in the architecture plan:
> **Critical Fact:** The standard Kaggle Emergency Vehicle dataset is **classification-only** (image + binary label), not an object detection dataset with bounding box annotations (`.txt` or Pascal VOC `.xml`).

Because there are no bounding boxes in the raw dataset, you cannot train an object detection YOLO model (`yolov8n.pt`) directly on it.

### The Two-Stage Computer Vision Design:
1. **Stage 1 (Vehicle Detection)**: Pretrained COCO YOLOv8 (`yolov8n.pt`) localizes vehicles in the camera frame (`car`, `bus`, `truck`, `motorcycle`).
2. **Stage 2 (Emergency Classification)**: Bounding box crops are passed to **`yolov8n-cls`**, fine-tuned on this dataset to classify whether the vehicle is emergency or normal.

---

## 3. Data Preparation & Directory Layout

`ml/prepare_data.py` inspects the raw data format and automatically supports:
1. **Kaggle CSV format**: `train.csv` (columns: `image_names`, `emergency_or_not`) + `images/` directory.
2. **Folder-based format**: Raw images stored in `emergency/` and `normal/` (or `non_emergency/`) folders.

It performs a **stratified, deterministic 70% / 15% / 15% split** (`seed=42`) and organizes the files into Ultralytics YOLO classification format:

```
data/ev_cls/
├── train/
│   ├── emergency/
│   └── normal/
├── val/
│   ├── emergency/
│   └── normal/
├── test/
│   ├── emergency/
│   └── normal/
└── split_meta.json
```

---

## 4. How to Train the Model

### Option A: Local Training (if GPU or fast CPU is available)
```bash
# 1. Prepare dataset split
python ml/prepare_data.py path/to/raw/kaggle_data --out_dir data/ev_cls --seed 42

# 2. Train YOLOv8n-cls
python ml/train_cls.py data/ev_cls --epochs 30 --imgsz 224

# 3. Evaluate on test split (produces ml/results/metrics.json)
python ml/evaluate_cls.py ml/runs/cls_train/weights/best.pt data/ev_cls
```

### Option B: Google Colab (Free T4 GPU, ~15-20 minutes)
1. Open [ml/colab_train.ipynb](../ml/colab_train.ipynb) in Google Colab.
2. Follow the numbered steps to download the Kaggle dataset, run training, and download:
   - `best.pt` (the fine-tuned weights)
   - `metrics.json` (precision, recall, false alarm rate, confusion matrix)

---

## 5. Connecting Model Metrics to Simulation

In the simulation, SUMO generates geometric vehicles rather than camera video frames. To assess how real camera perception errors affect the traffic controller:

1. `ml/evaluate_cls.py` writes `metrics.json` containing:
   - `ev_recall` (e.g. $0.95$)
   - `ev_false_alarm` (e.g. $0.01$)
2. These measured empirical rates are supplied directly to `NoisyEmulator` in `configs/exp_main.yaml`:
   ```yaml
   perception:
     provider: noisy
     noisy:
       ev_recall: 0.95
       ev_false_alarm: 0.01
       confirmation_k: 2
       confirmation_n: 3
   ```
This provides an empirically validated, noise-resilient evaluation of the traffic signal system.
