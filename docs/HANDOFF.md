# Research Handoff

最終更新：2026-08-24

## この文書の役割

このファイルを研究再開時の一次情報とする。新しいチャットは、最初にルートのREADME.md、このHANDOFF.md、研究計画、Notebookを確認すること。

Thammasat_MRI_Adversarial_Research_Handoff.docxは過去の会話時点で作成された旧資料であり、テスト評価の状態とεの候補が古い。現在の進捗判断には使用しない。

## 研究の目的

MobileNetV2を用いたMRI脳腫瘍4クラス分類モデルにuntargeted white-box FGSMを適用し、摂動強度εに応じて分類性能がどの程度低下するかを測定する。主目的はモデルの脆弱性評価であり、Adversarial Trainingは第二段階とする。

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

## 次に行う作業

1. ColabでNotebookを開き、Driveをマウントする。
2. データセット作成セルまで実行し、class_namesを準備する。
3. 保存済みモデルをロードし、通常テストAccuracyが再現することを確認する。
4. FGSMセクションを実行する。
5. ε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1でTestingデータ全体を評価する。
6. `fgsm_fine_summary.csv`、`fgsm_fine_class_metrics.csv`、グラフ、可視化画像を保存する。
7. 結果が単調に変化するか、クラス別の影響が異なるかを確認する。
8. 実測結果をREADME、研究計画、この文書へ反映する。

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

- 小さいεでのFGSM再実験は未実行
- ε = 1, 2, 4, 8の非単調なAccuracyは、攻撃がすでにほぼ飽和した後の揺らぎの可能性がある。微小ε領域の結果で確認する
- データセットが患者単位で独立に分割されているか未確認
- 保存済みモデルのファイルハッシュは未記録
- requirements.txtを作成済み。TensorFlow 2.20.0のみ元のColab出力で確認済みであり、その他の正確なバージョンは未記録

## 新しいチャットへの依頼文

~~~text
このリポジトリのREADME.md、docs/HANDOFF.md、
docs/thammasat_adversarial_examples_research_plan.md、
brain_tumor_adversarial_examples.ipynbを確認してください。
現在、MobileNetV2の通常テスト精度83.19%、詳細分類評価、
ε=0,1,2,4,8のFGSM予備実験まで完了しています。
次は0–255入力スケールのuntargeted white-box FGSMを
ε=0,0.01,0.05,0.1,0.25,0.5,1で再実験してください。
未確認の結果を推測で埋めないでください。
~~~
