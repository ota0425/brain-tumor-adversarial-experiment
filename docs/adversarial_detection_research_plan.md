# Adversarial Attack Detection 研究計画

最終更新：2026-08-24

## 1. 位置づけ

本計画は、MRI脳腫瘍4クラス分類モデルに対するFGSM脆弱性評価の次段階として、入力画像が通常画像（clean）か敵対的画像（adversarial）かを判定する検知モデルを構築・評価するものである。

本研究はThammasat Universityで実施し、毎日、指導教員Mr. Surasakと英語で研究ミーティングを行う。そのため、各Stepの確認済み結果、解釈、次の実験方針を英語で説明できるように整理する。

検知は分類結果を強制的に正す処理ではない。攻撃の疑いがある入力に対し、分類結果の採用を拒否し、人間の確認へ回すための安全機構として扱う。

## 2. 研究目的

1. MobileNetV2の内部特徴を利用し、clean/adversarialを判定する二値検知モデルを作る。
2. 学習に使用したFGSMのεに対する検知性能を測定する。
3. 学習に使用していないεに対する汎化性能を測定する。
4. 発展実験として、PGDなど未学習の攻撃へ汎化できるか確認する。
5. 検知した入力を拒否する場合の、検知率、誤警報率、最終的な分類安全性を評価する。

## 3. Research Questions

### RQ1：検知性能

> MobileNetV2の内部特徴を利用した二値検知モデルは、MRIのclean画像とFGSM adversarial画像を識別できるか。

### RQ2：未知のεへの汎化

> 一部のεで学習した検知モデルは、学習時に使用していないεのFGSM画像も検知できるか。

### RQ3：未知の攻撃への汎化（発展）

> FGSMで学習した検知モデルは、PGDなど別の攻撃に対しても検知性能を維持できるか。

## 4. システム構成

~~~text
MRI画像
  ├─ 既存の腫瘍分類モデル → glioma / meningioma / notumor / pituitary
  └─ adversarial検知モデル → clean / adversarial
                                         ├─ clean：分類結果を採用
                                         └─ adversarial：判定を拒否し人間へ回す
~~~

実際の攻撃時に元画像が手元にあるとは限らないため、検知モデルには判定対象のMRI画像1枚だけを入力する。元画像と攻撃画像の差分を直接入力する方式は、参考実験にはなるが主方式にはしない。

## 5. 検知モデルの初期設計

既存分類モデルのMobileNetV2から内部特徴を取り出し、二値検知ヘッドを学習する。

~~~text
MobileNetV2の中間または最終特徴
  → Global Average Pooling
  → Dense(128, ReLU)
  → Dropout
  → Dense(1, Sigmoid)
~~~

初期実験ではMobileNetV2を凍結し、検知ヘッドだけを学習する。性能が不十分な場合は、中間レイヤの特徴、複数レイヤの特徴結合、または入力画像を直接学習するCNNと比較する。

## 6. 検知用データセット

### 教師ラベル

| 入力 | 検知ラベル |
|---|---:|
| Clean MRI | 0 |
| FGSM adversarial MRI | 1 |

ε = 0の画像はcleanと同一であるため、adversarialクラスには含めない。

### データリーケージ防止

1. 元のMRI画像をTraining、Validation、Testingに分ける。
2. 分割後、各split内でのみadversarial画像を生成する。
3. 同じ元画像から作ったclean/adversarialペアを異なるsplitに入れない。
4. 可能な場合は患者単位でsplitを分離する。現データセットの患者ID情報は未確認のため、この点を制約として報告する。
5. 腫瘍クラスとεの構成比が大きく偏らないようにする。

## 7. εの学習・評価分割

微小ε実験の結果、Attack Success Rateはε=0.01の2.78%からε=1の96.02%まで単調に増加した。性能低下の立ち上がりを含むように、検知器の学習用εと未知εを次のとおり確定する。

| 用途 | ε（0–255スケール） |
|---|---|
| Clean | 0 |
| 検知器の学習 | 0.01, 0.1, 0.5 |
| 既知εの評価 | 0.01, 0.1, 0.5 |
| 未知εの評価 | 0.05, 0.25, 1 |

ε=0.05とε=0.25は学習値の間にある未知摂動として補間的な汎化を評価し、ε=1は学習範囲外の強い攻撃として外挿的な汎化を評価する。

## 8. 評価指標

- Detection Accuracy
- Precision、Recall、F1-score
- ROC-AUC、PR-AUC
- True Positive Rate（adversarial検知率）
- False Positive Rate（cleanの誤警報率）
- 混同行列
- ε別の検知率
- 腫瘍クラス別の検知率
- TPR at FPR = 1%など、誤警報率を固定した検知性能
- 検知器と分類器を組み合わせた場合のcoverageと分類性能

医療画像をcleanであるにもかかわら攻撃と判定するFalse Positiveは、実用上大きな問題となる。Accuracyだけでなく、必ずFalse Positive Rateを個別に報告する。

## 9. 実験段階

### Phase A：FGSM検知のProof of Concept

1. **完了**：微小εのFGSM評価を完了する。
2. **Notebook実装済み・Colab実行待ち**：Training/Validation画像から検知用データを生成する。
3. MobileNetV2の特徴を使った二値検知モデルを学習する。
4. 既知εに対する検知性能を評価する。

### Phase B：汎化性能

1. 未知のεで評価する。
2. 学習εと評価εの組み合わせを変える。
3. クラス別とε別の検知性能を比較する。

### Phase C：別攻撃とadaptive attack（発展）

1. PGDまたはBIMを実装し、FGSMで学習した検知器を評価する。
2. 分類器と検知器の両方を考慮したadaptive attackの脅威を考察する。
3. 必要に応じてAdversarial Trainingと検知器を比較する。

## 10. Notebookと成果物の分離

### 既存Notebook

`brain_tumor_adversarial_examples.ipynb`

- データセット確認
- 腫瘍4クラス分類モデルの学習
- Cleanベースライン評価
- FGSM生成
- ε別の脆弱性評価

### 検知実験用の新規Notebook

`brain_tumor_adversarial_detection.ipynb`

- **Step 1実装済み**：Colab環境、データセット、既存の保存済み分類モデルを再現する
- **Step 2実装済み**：バッチ単位で検知用clean/adversarialデータを生成する
- **Step 3実装済み**：MobileNetV2内部特徴を使う検知モデルを学習する
- 既知ε、未知ε、未知攻撃を評価する
- 検知結果をCSVとグラフへ保存する

検知実験を既存Notebookに追記することも技術的には可能である。しかし、攻撃実験の確定結果と検知器の学習状態、データ分割、評価結果が混在するため、再現性と説明のしやすさを優先して分離する。

## 11. 実装ステップ

### Step 1：実験基盤（実装済み）

- Colab、TensorFlow、GPU、乱数シードを設定する。
- 画像データと保存済み分類モデルを読み込む。
- clean Test Accuracy 83.19%前後を再現する。

### Step 2：検知データ（実装済み、Colab実行待ち）

- `tf.data`上でバッチ単位にFGSMを生成し、大量の画像ファイル複製を避ける。
- clean=0とadversarial=1を1:1にする。
- 学習ではε=0.01, 0.1, 0.5をバッチごとに循環させる。
- ValidationとTestingはεごとに固定したパイプラインを作る。
- Testingは検知閾値の調整に使用しない。
- 全FGSM画像をadversarialとし、攻撃成功画像と失敗画像の検知率は後で分けて報告する。

### Step 3：検知モデル学習（実装済み、Colab実行待ち）

- MobileNetV2を凍結し、内部特徴に二値検知ヘッドを接続する。
- Binary Crossentropy、Adam、最大20 epoch、EarlyStoppingを初期条件とする。
- Validation ROC-AUCまたはPR-AUCを基準にベストモデルを保存する。
- ベストモデル、学習履歴CSV、Loss・Accuracy・ROC-AUC・PR-AUCの曲線をGoogle Driveへ保存する。

### Step 4：既知εの評価

- 学習に含めたε=0.01, 0.1, 0.5を個別に評価する。
- Accuracy、Precision、Recall、F1、ROC-AUC、PR-AUC、FPRを報告する。

### Step 5：未知εの評価

- 学習に含めないε=0.05, 0.25, 1を個別に評価する。
- 既知εと未知εの性能差を汎化性能として考察する。

### Step 6：閾値と統合評価

- 検知閾値はValidationだけで決定し、Testingで調整しない。
- 基本閾値0.5に加え、FPR=1%以下となる閾値を評価する。
- cleanの正常採用、adversarialの正常拒否、cleanの誤拒否、adversarialの見逃しを報告する。

### Step 7：発展評価

- PGDなど未学習攻撃への汎化を評価する。
- 検知器を考慮したadaptive attackの脅威を考察する。
- Adversarial Trainingと検知器の役割と性能を比較する。

## 12. 主な制約

- 検知器は特定のFGSMやεの模様を記憶する可能性がある。
- 既知攻撃の高い検知率だけで、未知攻撃への安全性を主張しない。
- 検知器の存在を知る攻撃者は、分類器と検知器の両方を回避する攻撃を設計できる。
- 検知はAdversarial Trainingの代替とは限らない。
- 医療判断へ直接使用できるシステムではなく、実験的な脆弱性・検知可能性の評価である。

## 13. 参考文献

- Metzen et al., [On Detecting Adversarial Perturbations](https://arxiv.org/abs/1702.04267)
- Carlini and Wagner, [Adversarial Examples Are Not Easily Detected](https://arxiv.org/abs/1705.07263)
- Finlayson et al., [Adversarial attacks against medical deep learning systems](https://arxiv.org/abs/1804.05296)
