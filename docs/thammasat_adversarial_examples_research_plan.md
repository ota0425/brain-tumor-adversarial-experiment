# Thammasat University 研究計画

## 1. 研究の概要

- **研究期間**：約2か月
- **研究場所**：Thammasat University
- **担当教員**：Mr. Surasak
- **研究分野**：Cybersecurity in Machine Learning
- **主題**：Adversarial Examples（敵対的サンプル）
- **現在の進捗**：MobileNetV2を用いたMRI画像分類モデルの学習と、通常のテスト画像に対するベースライン評価まで完了している。
- **次の実験**：FGSMで敵対的サンプルを生成し、攻撃前後の分類性能を比較する。

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
4. **完了**：通常のテスト画像に対するAccuracy、Precision、Recall、F1-score、混同行列を測定する。
5. **次に実施**：TensorFlowのGradientTapeを用い、入力画像に対する損失の勾配からFGSMを実装する。
6. 複数のεでテスト画像から敵対的サンプルを生成する。生成後の画素値は元の入力範囲にクリップする。
7. 各εについてAccuracy、クラス別指標、Attack Success Rateを測定し、攻撃前と比較する。
8. 元画像、摂動、敵対的サンプルを表示し、攻撃強度と視覚的変化を確認する。
9. εとAccuracy、Accuracy Drop、Attack Success Rateの関係を表とグラフにまとめ、モデルの脆弱性を考察する。
10. **第二段階**：Adversarial Trainingを適用し、防御前後の通常性能と攻撃時性能を比較する。

### FGSM実装時の入力スケール

現在のNotebookでは、image_dataset_from_directoryが返す画像の画素値は0–255であり、mobilenet_v2.preprocess_inputはモデル内部に含まれている。そのため、入力画像に直接FGSMを適用する場合のεは **0–255スケール** で定義する。予備実験では、例えばε = 1, 2, 4, 8を候補とする。

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
| Accuracy |  |  |  |  |  |
| Accuracy Drop | 0 |  |  |  |  |
| Attack Success Rate | 0 |  |  |  |  |

※ 表のεは0–255の入力スケールに対する候補値であり、予備実験の結果に応じて調整する。

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

ただし、形式的検証は発展課題とし、最初に「MRI分類モデルの作成 → FGSM攻撃 → 防御評価」を完成させる。

## 11. 最低限の達成目標

- MRI画像分類モデルが動作する。（完了）
- FGSMによる敵対的サンプルを生成できる。
- εと分類性能の関係を定量的に示せる。
- 攻撃前後のAccuracy、Accuracy Drop、Attack Success Rateを比較できる。
- 実験方法、結果、考察を英語で説明できる。

Adversarial Training前後の比較は、上記を完成した後の追加目標とする。

## 12. 発展課題

- PGDなど、FGSM以外の攻撃手法との比較
- 複数モデル間での敵対的サンプルのTransferability評価
- 自動運転画像や交通標識画像への応用
- 攻撃・防御戦略のゲーム理論モデル化
- PRISMまたはPRISM-gamesを利用した安全性・セキュリティ特性の評価

## 13. 情報源

- [TensorFlow: Adversarial example using FGSM](https://www.tensorflow.org/tutorials/generative/adversarial_fgsm)
- [Kaggle: Brain Tumor MRI Dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset)
- Mr. Surasakの博士論文：*Rational Verification for Stackelberg Security Games*
