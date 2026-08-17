# Research Handoff

最終更新：2026-08-18

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

## 修正済みだが再実行が必要

Notebookの詳細分類評価セルは、prefetch適用後のtest_dataset.class_namesへアクセスしたため、次のエラーで停止していた。

~~~text
AttributeError: '_PrefetchDataset' object has no attribute 'class_names'
~~~

class_namesはprefetch前にすでに保存されているため、既存変数を使うようコードを修正した。修正後のセルはまだColabで実行していない。混同行列、Precision、Recall、F1-scoreは未取得として扱うこと。

## 次に行う作業

1. ColabでNotebookを開き、Driveをマウントする。
2. データセット作成セルまで実行し、class_namesを準備する。
3. 保存済みモデルをロードする。
4. 詳細分類評価セルを実行する。
5. 混同行列とclassification reportをNotebookへ保存する。
6. FGSM生成関数を実装する。
7. ε = 0, 1, 2, 4, 8でTestingデータ全体を評価する。
8. Accuracy、Accuracy Drop、Attack Success Rate、クラス別指標を表にする。
9. 元画像、摂動、敵対的画像の例を可視化する。
10. 結果を研究計画とこの文書へ反映する。

## FGSMの実装条件

- 攻撃：untargeted white-box FGSM
- 損失：sparse categorical crossentropy
- 勾配：損失の入力画像に対する勾配
- 入力スケール：0–255
- 初期ε候補：0, 1, 2, 4, 8
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

- 修正後の詳細分類評価セルは未実行
- FGSMコードと攻撃結果は未作成
- データセットが患者単位で独立に分割されているか未確認
- 保存済みモデルのファイルハッシュは未記録
- requirements.txtを作成済み。TensorFlow 2.20.0のみ元のColab出力で確認済みであり、その他の正確なバージョンは未記録

## 新しいチャットへの依頼文

~~~text
このリポジトリのREADME.md、docs/HANDOFF.md、
docs/thammasat_adversarial_examples_research_plan.md、
brain_tumor_adversarial_examples.ipynbを確認してください。
現在、MobileNetV2の通常テスト精度83.19%まで確認済みです。
最初に修正済みの詳細分類評価セルをColabで再実行し、
その後、0–255入力スケールのuntargeted white-box FGSMを
ε=0,1,2,4,8で実装・評価してください。
未確認の結果を推測で埋めないでください。
~~~
