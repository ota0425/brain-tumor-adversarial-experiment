"""Create concise English copies of the three research notebooks."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


MARKDOWN = {
    "brain_tumor_adversarial_examples.ipynb": {
        "yhWjeTj3tTWb": """# Adversarial Examples for Brain Tumor MRI Classification

## 1. Environment

Check the TensorFlow version and GPU availability.
""",
        "jsiwFzrltejY": """## 2. Dataset

Mount Google Drive and extract the Brain Tumor MRI Dataset in Colab.
""",
        "3gUdTcTNtiVh": """## 3. Dataset size

Count the Training and Testing images in each class.
""",
        "wzieV3hyuGaN": """## 4. Sample images

Display two images from each class to verify the dataset.
""",
        "RVtiZX8mvGTW": """## 5. TensorFlow datasets

Use 80% of the Training folder for training and 20% for validation. Reserve the Testing folder for final evaluation. Resize all images to 224 x 224.
""",
        "7nuYo52bvdQ-": """## 6. MobileNetV2 classifier

Use ImageNet-pretrained MobileNetV2. Freeze the backbone and train only the classification head.
""",
        "3dFLL4TnwDwS": """## 7. Baseline training

Train the classification head and save the model with the best validation accuracy to Google Drive.
""",
        "pfh5lyoPf6uo": """## 8. Baseline test evaluation

Evaluate the best saved model on the untouched Testing set. This result is the clean baseline for the FGSM experiments.
""",
        "Ki8YsC91jD6X": """### 8.1 Result

- Test loss: 0.5203
- Test accuracy: 0.8319 (83.19%)

The best validation accuracy was 91.071%, while the untouched Testing accuracy was 83.19%.
""",
        "J2yzNxO9jGyC": """## 9. Detailed classification metrics

Calculate the confusion matrix, precision, recall, and F1-score on the Testing set.
""",
        "o0MAfhx9Fgxu": r"""## 10. FGSM attack

Apply an untargeted white-box FGSM attack to the saved classifier. The model accepts images on a 0-255 scale, so epsilon uses the same scale.

Evaluate epsilon = 0, 0.01, 0.05, 0.1, 0.25, 0.5, and 1. An attack is successful when an initially correct prediction becomes incorrect.

\[
x_{adv} = \mathrm{clip}(x + \epsilon \cdot \mathrm{sign}(\nabla_x J(model(x), y)), 0, 255)
\]
""",
    },
    "brain_tumor_adversarial_detection.ipynb": {
        "title": """# Adversarial Attack Detection for Brain Tumor MRI

Build a binary detector that classifies an MRI image as clean or adversarial using an existing four-class MobileNetV2 classifier.

1. Prepare the experiment
2. Generate clean and adversarial detection data
3. Train a detector on MobileNetV2 features
4. Fine-tune the upper MobileNetV2 layers
5. Evaluate known and unseen epsilon values
""",
        "step-1": """## Step 1. Experiment setup

Load the dataset and classifier, verify matching class order, and reproduce approximately 83.19% clean Testing accuracy on 1,600 images.
""",
        "drive-and-paths-heading": """### 1.1 Drive and paths

Use the same dataset ZIP and saved classifier as the attack experiment.
""",
        "datasets-heading": """### 1.2 Datasets

Recreate the original split with the same image size, batch size, and seed. Verify that Training and Validation contain no overlapping source paths.
""",
        "classifier-heading": """### 1.3 Classifier check

Load the saved classifier and confirm its clean Testing performance before generating attacks.
""",
        "stop-point": """## Step 1 checkpoint

Confirm that `Step 1 completed` is displayed.

- Training epsilon: 0.01, 0.1, 0.5
- Unseen evaluation epsilon: 0.05, 0.25, 1.0
""",
        "step-2": """## Step 2. Detection data

Apply untargeted white-box FGSM and label clean MRI images as 0 and all FGSM images as 1. Generate each batch with `tf.data` without changing the classifier weights.
""",
        "training-detection-pipeline-heading": """### 2.1 Training pipeline

Assign epsilon 0.01, 0.1, and 0.5 across Training batches. Pair each clean image with one adversarial image to keep the labels balanced.
""",
        "evaluation-detection-pipelines-heading": """### 2.2 Validation and Testing

Use Validation for model selection and Testing only for final evaluation. Report each known and unseen epsilon separately.
""",
        "step-2-sanity-heading": """### 2.3 Data check

Verify the image range, balanced labels, and maximum perturbation using one batch at epsilon 0.1.
""",
        "step-2-stop-point": """## Step 2 checkpoint

Confirm that `Step 2 completed` is displayed and that the perturbation does not exceed epsilon.
""",
        "step-3": """## Step 3. Detector using MobileNetV2 features

Use the 1,280-dimensional `GlobalAveragePooling2D` output from the frozen classifier, followed by Dense(128), Dropout(0.3), and a sigmoid output.
""",
        "detector-training-heading": """### 3.1 Training settings

- Loss: Binary Crossentropy
- Optimizer: Adam, learning rate 0.001
- Maximum epochs: 20
- Model selection: Validation ROC-AUC
- Early stopping patience: 4

Testing and unseen epsilon values are excluded from model selection.
""",
        "step-3-validation-heading": """### 3.2 Validation

Evaluate the best frozen detector on Validation using threshold 0.5.
""",
        "step-3-stop-point": """## Step 3 checkpoint

Confirm that the frozen baseline model, configuration, metrics, history, and curves are saved to Google Drive.
""",
        "step-3b-fine-tuning": """## Step 3B. Fine-tuning

Start from the frozen detector, unfreeze the upper 30 MobileNetV2 layers, keep Batch Normalization frozen, and use a learning rate of 1e-5. Saved artifacts prevent unnecessary retraining.
""",
        "evaluate-fine-tuned-detector-heading": """### 3B.1 Fine-tuned Validation evaluation

Evaluate the best fine-tuned model at threshold 0.5 and compare it with the frozen baseline.
""",
        "step-3b-stop-point": """## Step 3B checkpoint

Compare Binary Accuracy, ROC-AUC, PR-AUC, Recall, and FPR. Then evaluate known and unseen epsilon values on Testing.
""",
        "step-4-test-evaluation": """## Step 4. Final Testing evaluation by epsilon

Fix the best fine-tuned model and threshold at 0.5. Evaluate each known and unseen epsilon without using Testing for model or threshold selection. Also report attack success and detection rates.
""",
        "step-4-stop-point": """## Step 4 checkpoint

Confirm that `Step 4 completed` is displayed. Treat any later model or threshold change as a new Validation-selected experiment to avoid overfitting to Testing.
""",
    },
    "brain_tumor_adversarial_detection_v2.ipynb": {
        "title": """# Small-Perturbation Adversarial Attack Detection (Experiment 2)

Experiment 1 is retained as a baseline. This experiment detects small FGSM attacks that change a correct diagnosis into an incorrect one.

- Features: classifier probabilities, internal features, and consistency before and after light blur
- Positive class: successful attacks
- Negative class: clean images
- Threshold: selected on Validation with FPR <= 10%
- Testing: used only after fixing the model and threshold
""",
        "setup-heading": "## Step 1. Prepare Drive, data, and classifier\n",
        "features-heading": """## Step 2. Generate FGSM and detection features

Blur is used to measure prediction and feature consistency, not as a defense.
""",
        "training-heading": "## Step 3. Train a new successful-attack detector\n",
        "threshold-heading": """## Step 4. Select a threshold on Validation

Select the best threshold with FPR <= 10%. Do not use Testing for threshold selection.
""",
        "test-heading": "## Step 5. Final Testing evaluation with the fixed model and threshold\n",
        "fair-comparison-heading": """## Step 6. Fair comparison of Experiments 1 and 2

Evaluate both models on the same Testing images, FGSM images, and successful-attack subsets. Report ROC-AUC and PR-AUC for clean vs all attacks and clean vs successful attacks.
""",
        "interpretation": """## Evaluation criteria

The main target is a successful-attack detection rate of at least 80% with a clean false-positive rate of at most 10%.
""",
    },
}


CODE_REPLACEMENTS = {
    'print("展開完了")': 'print("Extraction completed")',
    "# MobileNetV2の学習済み部分を固定": "# Freeze the pretrained MobileNetV2 backbone",
    "# データ読み込みを高速化": "# Improve input pipeline performance",
    "# モデルの保存先": "# Model output directory",
    "# 保存したベストモデルのパス": "# Path to the best saved model",
    "# モデルが存在するか確認": "# Check that the model exists",
    "# ベストモデルを読み込み": "# Load the best model",
    "# 未使用のTestingデータで評価": "# Evaluate on the untouched Testing set",
    "# class_namesはprefetch適用前（セル13）に保存済み": "# class_names was saved before prefetching",
    "# PrefetchDatasetにはclass_names属性がないため、既存の変数を使用する": "# PrefetchDataset has no class_names attribute",
    "# labelsがone-hotの場合": "# Handle one-hot labels",
    "# 0–255入力スケール上の摂動強度": "# Perturbation strength on the 0-255 input scale",
    "入力画像に対する損失勾配の符号を計算する。": "Return the sign of the loss gradient with respect to the input.",
    "modelは確率（softmax）を出力するため、from_logits=Falseを使用する。": "The model returns softmax probabilities, so from_logits=False.",
    "FGSMによる敵対的画像を作成し、画素値を0–255に制限する。": "Create an FGSM image and clip pixel values to 0-255.",
    "# 各εの予測結果を保存": "# Store predictions for each epsilon",
    "# clean画像の予測とFGSM方向を1回だけ計算": "# Compute clean predictions and the FGSM direction once",
    "# 同じ勾配方向を使用して各εの敵対的画像を評価": "# Evaluate each epsilon using the same gradient direction",
    "# cleanでは正解、攻撃後は不正解になった画像": "# Initially correct images that become incorrect after attack",
    "# テストデータの最初のバッチを取得": "# Get the first Testing batch",
    "# 摂動を見やすい0–1範囲に変換": "# Scale the perturbation to 0-1 for display",
}


def replace_output_text(value):
    if isinstance(value, dict):
        return {key: replace_output_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_output_text(item) for item in value]
    if isinstance(value, str):
        return value.replace("展開完了", "Extraction completed")
    return value


for source_name, markdown_cells in MARKDOWN.items():
    source_path = ROOT / source_name
    notebook = json.loads(source_path.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        cell_id = cell.get("metadata", {}).get("id")
        if cell["cell_type"] == "markdown" and cell_id in markdown_cells:
            cell["source"] = markdown_cells[cell_id].splitlines(keepends=True)
        elif cell["cell_type"] == "code":
            source = "".join(cell.get("source", []))
            for old, new in CODE_REPLACEMENTS.items():
                source = source.replace(old, new)
            cell["source"] = source.splitlines(keepends=True)
        cell["outputs"] = replace_output_text(cell.get("outputs", []))

    target_path = ROOT / source_name.replace(".ipynb", "_en.ipynb")
    target_path.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print("Created:", target_path.name)
