# Thammasat University 研究計画

## 1. 研究の概要

- **研究期間**：約2か月
- **研究場所**：Thammasat University
- **担当教員**：Mr. Surasak
- **研究ミーティング**：毎日、指導教員と英語で進捗、実験結果、次の研究方針を確認する。
- **研究分野**：Cybersecurity in Machine Learning
- **主題**：Adversarial Examples（敵対的サンプル）
- **現在の進捗**：MobileNetV2の学習、通常テスト評価、詳細分類評価、予備実験、ε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1のFGSM微小摂動実験まで完了している。
- **次の実験**：clean/adversarial二値検知モデルを構築し、既知εと未知εで評価する。

確認済みのベースライン結果は、最高Validation Accuracyが0.91071、通常Testingデータ1,600枚に対するTest Lossが0.5203、Test Accuracyが0.8319（83.19%）である。混同行列およびクラス別Precision、Recall、F1-scoreも取得済みである。

## 2. 研究テーマ案

### 英語

**Adversarial Attacks and Defenses for Brain Tumor Classification Using MRI Images**

### 日本語

**MRI画像を用いた脳腫瘍分類に対する敵対的攻撃と防御の評価**

## 3. 研究目的

MRI画像を分類する機械学習モデルに対してFGSM（Fast Gradient Sign Method）による敵対的サンプルを生成し、小さな摂動によって分類性能がどの程度低下するかを定量的に調査する。主な目的は、攻撃前後のAccuracyと複数のεにおける性能変化を比較し、現在の分類モデルの **脆弱性** を明らかにすることである。

Adversarial Trainingによる防御評価は、FGSM攻撃と脆弱性評価が完了した後の第二段階とする。

## 4. Research Question

> MobileNetV2を用いたMRI画像分類モデルは、FGSMによる小さな摂動に対してどの程度Accuracyが低下するのか。また、摂動強度εと性能低下の間にどのような関係があるか。

### 第二段階のResearch Question

> Adversarial Trainingを適用することで、通常画像に対する性能を大きく損なわずに、FGSMに対する頑健性を改善できるか。

## 5. MRI画像を優先する理由

- 画像分類として問題を設定しやすい。
- 公開データセットを利用できる。
- TensorFlowのFGSMチュートリアルを応用しやすい。
- 自動運転画像を用いた物体検出よりも実験環境が単純であり、2か月で完了しやすい。
- 医療画像に対する誤分類のリスクという明確なセキュリティ上の意義がある。

自動運転画像については、MRI画像の実験が早く完了した場合の発展課題とする。

## 6. 実験の流れ

1. **完了**：KaggleのBrain Tumor MRI Datasetを取得し、データ構成とクラス数を確認する。
2. **完了**：Trainingデータを学習用80%と検証用20%に分割し、別のTestingデータを最終評価用とする。
3. **完了**：ImageNetで事前学習されたMobileNetV2の特徴抽出部を固定し、MRI画像4クラス分類モデルを学習する。
4. **完了**：通常のテスト画像に対するLoss、Accuracy、Precision、Recall、F1-score、混同行列を測定する。
5. **完了**：TensorFlowのGradientTapeを用い、入力画像に対する損失の勾配からFGSMを実装する。
6. **予備実験完了**：ε = 0, 1, 2, 4, 8でテスト画像から敵対的サンプルを生成し、各指標を測定する。
7. **完了**：ε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1で再実験し、性能低下の立ち上がりを詳細に測定する。
8. 元画像、摂動、敵対的サンプルを表示し、微小εにおける視覚的変化を確認する。
9. εとAccuracy、Accuracy Drop、Attack Success Rateの関係を表とグラフにまとめ、モデルの脆弱性を考察する。
10. **第二段階**：Adversarial Trainingを適用し、防御前後の通常性能と攻撃時性能を比較する。

### FGSM実装時の入力スケール

現在のNotebookでは、image_dataset_from_directoryが返す画像の画素値は0–255であり、mobilenet_v2.preprocess_inputはモデル内部に含まれている。そのため、入力画像に直接FGSMを適用する場合のεは **0–255スケール** で定義する。予備実験のε = 1, 2, 4, 8では攻撃がすでにほぼ飽和したため、次はε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1を使用する。

εを0–1スケールで表す場合は、実際に画像へ加える値を255 × εとし、どちらの定義を用いたかを結果に明記する。

## 7. 評価指標

- Accuracy
- Precision
- Recall
- F1-score
- Attack Success Rate
- εごとの性能低下量
- クラス別の性能変化と混同行列
- 敵対的サンプルの視覚的確認
- 第二段階ではAdversarial Training前後の性能差

Accuracy Dropは「通常画像のAccuracy − 敵対的サンプルのAccuracy」とする。Attack Success Rateは、**攻撃前に正しく分類されたテスト画像**のうち、FGSM後に誤分類となった割合とする。

## 8. 結果整理用の表

| 評価指標 | 通常画像 | FGSM ε=1 | FGSM ε=2 | FGSM ε=4 | FGSM ε=8 |
|---|---:|---:|---:|---:|---:|
| Accuracy | 0.8319 | 0.0331 | 0.0144 | 0.0187 | 0.0431 |
| Accuracy Drop | 0 | 0.7988 | 0.8175 | 0.8131 | 0.7888 |
| Attack Success Rate | 0 | 0.9602 | 0.9827 | 0.9775 | 0.9482 |

※ 表のεは0–255の入力スケールに対する予備実験の実測値である。

### 微小摂動の再実験（完了）

| 評価指標 | ε=0 | ε=0.01 | ε=0.05 | ε=0.1 | ε=0.25 | ε=0.5 | ε=1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Accuracy | 0.8319 | 0.8087 | 0.7056 | 0.5319 | 0.2081 | 0.0781 | 0.0331 |
| Accuracy Drop | 0.0000 | 0.0231 | 0.1263 | 0.3000 | 0.6238 | 0.7538 | 0.7988 |
| Attack Success Rate | 0.0000 | 0.0278 | 0.1518 | 0.3606 | 0.7498 | 0.9061 | 0.9602 |

### 確認済みのベースライン結果

| 指標 | 結果 |
|---|---:|
| Best Validation Accuracy | 0.91071 |
| Best Epoch | 9 |
| Test Loss | 0.5203 |
| Clean Test Accuracy | 0.8319（83.19%） |

## 9. 8週間の予定

| 期間 | 内容 | 成果物 |
|---|---|---|
| 第1週 | Adversarial Examples、FGSM、画像分類の基礎学習 | 調査メモ、環境構築 |
| 第2週 | データセットの確認、前処理、ベースライン設計 | データ分析結果 |
| 第3週 | MRI画像分類モデルの学習と評価 | ベースラインモデル |
| 第4週 | FGSMの実装と敵対的サンプルの生成 | 攻撃コード、生成画像 |
| 第5週 | εを変えた攻撃実験 | 実験結果の表とグラフ |
| 第6週 | Adversarial Trainingの実装と再実験 | 防御モデル、比較結果 |
| 第7週 | 結果分析、追加実験、考察 | 結果・考察の草稿 |
| 第8週 | レポートと発表資料の作成 | 最終レポート、スライド |

## 10. Mr. Surasakの専門との接続

Mr. Surasakの研究では、攻撃者と防御者の戦略、Stackelberg Security Games、PRISM-gamesによる形式的検証などが扱われている。時間に余裕がある場合、MRI画像分類の実験を次のような攻撃者・防御者モデルへ発展させられる。

- **攻撃者の戦略**：FGSMのεや攻撃対象を選択する。
- **防御者の戦略**：通常学習、Adversarial Trainingなどから防御方法を選択する。
- **評価値**：攻撃成功率、分類精度、防御コスト、計算コストなどを用いる。
- **発展目標**：攻撃と防御の条件をモデル化し、どの防御戦略が有効か分析する。

ただし、形式的検証は発展課題とし、最初に「MRI分類モデルの作成 → FGSM攻撃 → 脆弱性評価」を完成させる。防御評価はその後の第二段階とする。

## 11. 最低限の達成目標

- MRI画像分類モデルが動作する。（完了）
- 通常Testingデータに対するLossとAccuracyを測定できる。（完了：Accuracy 83.19%）
- 混同行列とクラス別Precision、Recall、F1-scoreを測定できる。（完了）
- FGSMによる敵対的サンプルを生成できる。（完了）
- εと分類性能の関係を定量的に示せる。（完了）
- 攻撃前後のAccuracy、Accuracy Drop、Attack Success Rateを比較できる。（完了）
- 実験方法、結果、考察を英語で説明できる。

Adversarial Training前後の比較は、上記を完成した後の追加目標とする。

Adversarial検知モデルは、攻撃実験の次段階の主要テーマとする。検知モデルのResearch Question、データ分割、検知指標、汎化評価は[Adversarial Attack Detection 研究計画](adversarial_detection_research_plan.md)に定義する。

## 12. 発展課題

- PGDなど、FGSM以外の攻撃手法との比較
- 複数モデル間での敵対的サンプルのTransferability評価
- 自動運転画像や交通標識画像への応用
- 攻撃・防御戦略のゲーム理論モデル化
- PRISMまたはPRISM-gamesを利用した安全性・セキュリティ特性の評価
- 元画像と敵対的画像の差異を学習し、敵対的入力を検知するモデルの構築
- 個別の攻撃を防ぐだけでなく、未知の攻撃にも汎化できる異常検知方法の検討

### Adversarial検知実験のNotebook

攻撃生成と脆弱性評価は既存の`brain_tumor_adversarial_examples.ipynb`に残す。検知モデルの学習と評価は、新しい`brain_tumor_adversarial_detection.ipynb`で実施する。これにより、攻撃実験の確定結果と検知器の学習状態、データ分割、評価結果を分離する。

## 13. 情報源

- [TensorFlow: Adversarial example using FGSM](https://www.tensorflow.org/tutorials/generative/adversarial_fgsm)
- [Kaggle: Brain Tumor MRI Dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset)
- Mr. Surasakの博士論文：*Rational Verification for Stackelberg Security Games*
