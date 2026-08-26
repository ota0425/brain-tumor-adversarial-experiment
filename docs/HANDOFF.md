# Research Handoff

最終更新：2026-08-26

## この文書の役割

このファイルを研究再開時の一次情報とする。新しいチャットは、最初にルートのREADME.md、このHANDOFF.md、研究計画、Notebookを確認すること。

Thammasat_MRI_Adversarial_Research_Handoff.docxは過去の会話時点で作成された旧資料であり、テスト評価の状態とεの候補が古い。現在の進捗判断には使用しない。

## 研究環境とコミュニケーション

- ユーザーはタイのThammasat University（タマサート大学）で本研究を実施している。
- 指導教員はMr. Surasakである。
- 毎日、研究進捗と実験方針について、指導教員と英語でミーティングを行っている。
- 新しいチャットは、実験実装だけでなく、英語ミーティングで使える進捗説明、結果の解釈、次に相談する質問の整理も支援する。
- 英語説明では、実測済みの事実、現時点の解釈、未確認事項を明確に分け、未実行の結果を推測で埋めない。

## 研究の目的

MobileNetV2を用いたMRI脳腫瘍4クラス分類モデルにuntargeted white-box FGSMを適用し、摂動強度εに応じて分類性能がどの程度低下するかを測定する。その次段階として、clean/adversarialを判定し、攻撃の疑いがある入力を拒否できる検知モデルを評価する。詳細は`docs/adversarial_detection_research_plan.md`を一次情報とする。

## 確認済みの構成

- クラス：glioma、meningioma、notumor、pituitary
- Training：5,600枚（各クラス1,400枚）
- Testing：1,600枚（各クラス400枚）
- Trainingの20%をvalidationとして使用
- 入力：224 × 224 × 3、画素値0–255
- モデル内部でMobileNetV2のpreprocess_inputを実行
- ImageNet事前学習済みMobileNetV2を凍結して使用
- TensorFlow 2.20.0、Colab T4 GPUで実行済み

## 完了済み

1. Google DriveのデータセットZIPをColabへ展開
2. データセットの画像数とクラス順を確認
3. MobileNetV2ベースラインを10 epoch学習
4. validation accuracyを基準にベストモデルを保存
5. 保存済みモデルをロード
6. 未加工のTestingデータ1,600枚でlossとaccuracyを測定

確認済み結果：

| 指標 | 結果 |
|---|---:|
| Best Validation Accuracy | 0.91071 |
| Best Epoch | 9 |
| Test Loss | 0.5203 |
| Test Accuracy | 0.8319（83.19%） |

## 詳細分類評価（完了）

Notebookの詳細分類評価セルは、prefetch適用後のtest_dataset.class_namesへアクセスしたため、次のエラーで停止していた。

~~~text
AttributeError: '_PrefetchDataset' object has no attribute 'class_names'
~~~

class_namesはprefetch前にすでに保存されているため、既存変数を使うようコードを修正した。修正後のセルはColabで実行済みである。

| クラス | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| glioma | 0.9317 | 0.6475 | 0.7640 | 400 |
| meningioma | 0.7094 | 0.7325 | 0.7208 | 400 |
| notumor | 0.8958 | 0.9675 | 0.9303 | 400 |
| pituitary | 0.8218 | 0.9800 | 0.8940 | 400 |

## FGSM予備実験（完了）

0–255入力スケールでε = 0, 1, 2, 4, 8を評価済みである。

| ε | Clean Accuracy | Adversarial Accuracy | Accuracy Drop | Attack Success Rate |
|---:|---:|---:|---:|---:|
| 0 | 0.8319 | 0.8319 | 0.0000 | 0.0000 |
| 1 | 0.8319 | 0.0331 | 0.7988 | 0.9602 |
| 2 | 0.8319 | 0.0144 | 0.8175 | 0.9827 |
| 4 | 0.8319 | 0.0187 | 0.8131 | 0.9775 |
| 8 | 0.8319 | 0.0431 | 0.7888 | 0.9482 |

ε = 1で攻撃後Accuracyが3.31%まで低下したため、性能低下が立ち上がる範囲を詳細に調べる追加実験が必要である。

## FGSM微小ε実験（完了）

| ε | Clean Accuracy | Adversarial Accuracy | Accuracy Drop | Attack Success Rate |
|---:|---:|---:|---:|---:|
| 0 | 0.8319 | 0.8319 | 0.0000 | 0.0000 |
| 0.01 | 0.8319 | 0.8087 | 0.0231 | 0.0278 |
| 0.05 | 0.8319 | 0.7056 | 0.1263 | 0.1518 |
| 0.10 | 0.8319 | 0.5319 | 0.3000 | 0.3606 |
| 0.25 | 0.8319 | 0.2081 | 0.6238 | 0.7498 |
| 0.50 | 0.8319 | 0.0781 | 0.7538 | 0.9061 |
| 1.00 | 0.8319 | 0.0331 | 0.7988 | 0.9602 |

εの増加に応じてAccuracyは単調に低下した。ε=0.05–0.25が性能低下の主な立ち上がり領域である。

## Adversarial検知初期実験（Step 1–3実行済み）

凍結済みMobileNetV2のGlobalAveragePooling2D特徴へ二値検知ヘッドを接続し、clean=0、FGSM adversarial=1として学習した。Validationは学習時と同じε=0.01, 0.1, 0.5を使用した。

ベストモデルを閾値0.5で評価した結果：

| 指標 | 結果 |
|---|---:|
| Binary Accuracy | 0.5408 |
| Loss | 0.7049 |
| ROC-AUC | 0.6520 |
| PR-AUC | 0.6552 |
| Precision | 0.8425 |
| Recall | 0.1003 |

Accuracyは50%に近く、Recallは約10%である。凍結した最終特徴だけではFGSM摂動を十分に識別できていない可能性がある。初回実行時はTrainingとValidationを異なるshuffle条件で別々に作成していたため、数値は予備結果として扱う。現在は`subset="both"`の1回の呼び出しで両方を作り、元画像pathの重複が0件であることをassertするコードへ修正済みである。修正後の再実行は未実施である。

## 2026-08-25 Mr. Surasakとの決定

- Detection Notebookの構成と初期結果を説明した。
- 現在の検知性能はランダム判定に近いと共有した。
- 改善方法として、凍結済みMobileNetV2のfine-tuningを行うことになった。
- 今週の主タスクはfine-tuningによる検知性能向上である。
- 暫定目標はBinary Accuracy約80%である。
- AccuracyだけでなくROC-AUC、PR-AUC、Recall、FPRも報告する。

## 次に行う作業

1. **コード修正済み・再実行待ち**：Training/Validationを1回の分割処理で作り、画像重複が0件であることを検証する。
2. 修正後のsplitで凍結モデルを再学習し、比較用baselineとして保存する。
3. MobileNetV2の上位層だけを解凍し、小さいlearning rateでfine-tuningする。
4. 同一split、seed、ε、epoch条件で凍結版とfine-tuning版を比較する。
5. Validation Binary Accuracy約80%を目標としつつ、ROC-AUC、PR-AUC、Recall、FPRも確認する。
6. モデル選択後、既知ε=0.01, 0.1, 0.5と未知ε=0.05, 0.25, 1をTestingで個別評価する。
7. fine-tuningだけで不十分な場合は、中間層・複数層特徴、入力画像CNN、feature squeezing、Mahalanobis距離などを比較候補とする。

作業上は「検知器のBinary CrossentropyでMobileNetV2上位層を検知ヘッドと共同fine-tuningする」と解釈する。ただし、先生の意図が「先に4クラスMRI分類モデルをfine-tuningしてから検知器を再構築する」でないか、次回ミーティングで確認する。

## FGSMの実装条件

- 攻撃：untargeted white-box FGSM
- 損失：sparse categorical crossentropy
- 勾配：損失の入力画像に対する勾配
- 入力スケール：0–255
- 微小摂動の再実験：0, 0.01, 0.05, 0.1, 0.25, 0.5, 1
- クリップ範囲：0–255
- 同じTestingデータをclean/attackの両方で使用

式：

~~~text
x_adv = clip(x + ε × sign(∇x J(model(x), y)), 0, 255)
~~~

Accuracy Drop：

~~~text
clean accuracy − adversarial accuracy
~~~

Attack Success Rate：

~~~text
攻撃前に正しく分類された画像のうち、攻撃後に誤分類となった画像の割合
~~~

## 保存場所

データセットZIP：

~~~text
/content/drive/MyDrive/ThammasatResearch/dataset/archive.zip
~~~

ベストモデル：

~~~text
/content/drive/MyDrive/ThammasatResearch/models/baseline_mobilenetv2.keras
~~~

データセットとモデルはGitHub管理外である。新しい実行環境ではGoogle Drive上のファイルが必要。

## 未確認事項・制約

- 検知初期実験は実行済み。Training/Validation splitのコードは修正済みだが、Colabでの再実験が必要
- Binary Accuracy約80%は暫定目標であり、RecallやFPRを無視して成功を判断しない
- データセットが患者単位で独立に分割されているか未確認
- 保存済みモデルのファイルハッシュは未記録
- requirements.txtを作成済み。TensorFlow 2.20.0のみ元のColab出力で確認済みであり、その他の正確なバージョンは未記録

## 新しいチャットへの依頼文

~~~text
このリポジトリのREADME.md、docs/HANDOFF.md、
docs/thammasat_adversarial_examples_research_plan.md、
docs/adversarial_detection_research_plan.md、
brain_tumor_adversarial_examples.ipynbを確認してください。
ユーザーはThammasat Universityで本研究を行っており、
毎日、指導教員Mr. Surasakと英語で研究ミーティングを行っています。
進捗、確認済みの結果、次の作業を英語で説明できる形で整理してください。
現在、MobileNetV2の通常テスト精度83.19%、詳細分類評価、
ε=0,1,2,4,8のFGSM予備実験、微小ε実験まで完了しています。
検知NotebookのStep 1からStep 3はColabで実行済みです。
初期検知結果はBinary Accuracy 0.5408、ROC-AUC 0.6520、PR-AUC 0.6552、
Precision 0.8425、Recall 0.1003で、予備的にはランダム判定に近い性能です。
Training/Validation splitは`subset="both"`を使うコードへ修正済みです。
まずColabで全セルを再実行し、重複0件を確認して凍結版baselineを更新してください。
その後、Mr. Surasakとの2026-08-25の決定に従い、MobileNetV2上位層を
小さいlearning rateでfine-tuningし、Binary Accuracy約80%を目標に、
ROC-AUC、PR-AUC、Recall、FPRも比較してください。
モデル選択後、既知ε=0.01,0.1,0.5と未知ε=0.05,0.25,1を個別評価してください。
未確認の結果を推測で埋めないでください。
~~~
