# Adversarial Attack Detection 研究計画

最終更新：2026-08-26

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

初期実験ではMobileNetV2を凍結し、検知ヘッドだけを学習した。Validation Binary Accuracy 0.5408、ROC-AUC 0.6520、Recall 0.1003となり、性能が不十分だった。2026-08-25のMr. Surasakとのミーティングで、次の主要実験としてMobileNetV2のfine-tuningを行うことを決定した。暫定目標はBinary Accuracy約80%とするが、ROC-AUC、PR-AUC、Recall、FPRも必ず併記する。

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
2. **コード修正済み・再実験必要**：Training/Validationを`subset="both"`で同時に作成し、重複0件を検証する。Colabでの再実行は未実施。
3. **初期実験完了**：凍結MobileNetV2の特徴を使った二値検知モデルを学習する。
4. **実装済み・実行待ち**：MobileNetV2上位30層をfine-tuningし、凍結版と比較する。
5. 既知εに対する検知性能を評価する。

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

### Step 2：検知データ（split修正実装済み、再実行待ち）

- `tf.data`上でバッチ単位にFGSMを生成し、大量の画像ファイル複製を避ける。
- clean=0とadversarial=1を1:1にする。
- 学習ではε=0.01, 0.1, 0.5をバッチごとに循環させる。
- ValidationとTestingはεごとに固定したパイプラインを作る。
- Testingは検知閾値の調整に使用しない。
- 全FGSM画像をadversarialとし、攻撃成功画像と失敗画像の検知率は後で分けて報告する。
- TrainingとValidationは`subset="both"`による1回の呼び出しで同時に作成するコードへ修正済みである。元画像pathの集合を比較し、重複0件、Training 4,480枚、Validation 1,120枚、合計5,600枚をassertする。Colabでの実測確認は次回実行時に行う。

### Step 3：凍結モデルの初期学習（実行済み）

- MobileNetV2を凍結し、内部特徴に二値検知ヘッドを接続する。
- Binary Crossentropy、Adam、最大20 epoch、EarlyStoppingを初期条件とする。
- Validation ROC-AUCまたはPR-AUCを基準にベストモデルを保存する。
- ベストモデル、学習履歴CSV、Loss・Accuracy・ROC-AUC・PR-AUCの曲線をGoogle Driveへ保存する。

初期Validation結果（閾値0.5）はBinary Accuracy 0.5408、Loss 0.7049、ROC-AUC 0.6520、PR-AUC 0.6552、Precision 0.8425、Recall 0.1003だった。split修正前のため予備結果として扱う。

### Step 3B：MobileNetV2 fine-tuning（実装済み、Colab実行待ち）

- 修正済みsplitで凍結版を同じ条件で再実行し、比較基準を確定する。
- 最初から全層を解凍せず、MobileNetV2の上位30層だけを解凍する。
- Batch Normalization層は初期比較では凍結を維持する。
- 検知ヘッドの学習済み重みから開始し、Adamと小さいlearning rate（初期候補1e-5）を使用する。
- Validation ROC-AUCをベストモデル基準として維持し、Binary Accuracy約80%を暫定目標とする。
- 凍結版とfine-tuning版を、同一split、seed、ε、指標で比較する。
- 凍結baselineとfine-tuningモデルは別名で保存する。各実験のモデルと学習履歴CSVが両方存在する場合は学習を自動スキップし、どちらかが欠けた途中状態では再学習する。強制再学習時だけ`FORCE_RETRAIN_* = True`とする。

### Fine-tuning以外の改善候補

1. GlobalAveragePooling2Dの最終特徴だけでなく、より浅い中間層または複数層の特徴を結合する。
2. MRI入力を直接受け取る小規模CNNを検知器として比較する。
3. εごとの性能を確認し、微小εと強いεを分けたcurriculumまたはsamplingを検討する。
4. 同一画像について複数εを学習へ含め、特定εへの依存を減らす。
5. Feature squeezing後の分類出力との不一致を検知スコアとして比較する。
6. 複数層特徴に対するMahalanobis距離またはLocal Intrinsic Dimensionalityを比較する。
7. FGSMで改善後、PGD/BIMを学習または評価へ追加し、攻撃手法への過適合を確認する。
8. 判定閾値はValidationで調整できるが、ROC-AUCそのものは改善しないため、モデル改善とは分けて報告する。

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
- Xu et al., [Feature Squeezing: Detecting Adversarial Examples in Deep Neural Networks](https://arxiv.org/abs/1704.01155)
- Ma et al., [Characterizing Adversarial Subspaces Using Local Intrinsic Dimensionality](https://arxiv.org/abs/1801.02613)
- Lee et al., [A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks](https://arxiv.org/abs/1807.03888)
- Carlini and Wagner, [Adversarial Examples Are Not Easily Detected](https://arxiv.org/abs/1705.07263)
- Finlayson et al., [Adversarial attacks against medical deep learning systems](https://arxiv.org/abs/1804.05296)
