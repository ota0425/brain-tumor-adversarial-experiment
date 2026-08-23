# Brain Tumor Adversarial Experiment

MRI画像の4クラス分類モデルにFGSM（Fast Gradient Sign Method）を適用し、攻撃前後の分類性能を比較する研究プロジェクトです。実験はGoogle ColabとTensorFlow/Kerasを使用します。

## 最初に読む資料

- [HANDOFF.md](docs/HANDOFF.md)：現在の正確な進捗、既知の問題、次の作業
- [研究計画](docs/thammasat_adversarial_examples_research_plan.md)：研究目的、Research Question、評価指標
- [実験Notebook](brain_tumor_adversarial_examples.ipynb)：データ読み込み、学習、評価、今後のFGSM実装
- [docs/README.md](docs/README.md)：参考資料の位置づけ

新しいCodexチャットでは、このフォルダを開いた状態で「README.mdとdocs/HANDOFF.mdを読み、次の作業を続けて」と依頼してください。

## 現在の進捗

| 項目 | 状態 |
|---|---|
| データセット確認 | 完了 |
| MobileNetV2ベースライン学習 | 完了 |
| 保存済みベストモデルの読み込み | 完了 |
| 未加工テスト画像でのAccuracy評価 | 完了 |
| 混同行列・Precision・Recall・F1-score | 完了 |
| FGSM実装 | 完了 |
| 予備実験（ε = 0, 1, 2, 4, 8） | 完了 |
| 小さいεの再実験 | Notebook修正済み、Colabで再実行が必要 |
| Adversarial Training | 第二段階 |

確認済みのベースライン結果：

- Validation Accuracy（最高）：**0.91071**（epoch 9）
- Test Loss：**0.5203**
- Test Accuracy：**0.8319（83.19%）**
- テスト画像数：1,600枚

通常画像のクラス別F1-score：

| クラス | Precision | Recall | F1-score |
|---|---:|---:|---:|
| glioma | 0.9317 | 0.6475 | 0.7640 |
| meningioma | 0.7094 | 0.7325 | 0.7208 |
| notumor | 0.8958 | 0.9675 | 0.9303 |
| pituitary | 0.8218 | 0.9800 | 0.8940 |

## FGSM予備実験の結果

0–255入力スケールでε = 0, 1, 2, 4, 8を評価しました。ε = 1でもAccuracyが3.31%まで低下したため、攻撃の影響が立ち上がる範囲を調べるために、より小さいεで再実験します。

| ε | Clean Accuracy | Adversarial Accuracy | Accuracy Drop | Attack Success Rate |
|---:|---:|---:|---:|---:|
| 0 | 0.8319 | 0.8319 | 0.0000 | 0.0000 |
| 1 | 0.8319 | 0.0331 | 0.7988 | 0.9602 |
| 2 | 0.8319 | 0.0144 | 0.8175 | 0.9827 |
| 4 | 0.8319 | 0.0187 | 0.8131 | 0.9775 |
| 8 | 0.8319 | 0.0431 | 0.7888 | 0.9482 |

次回の微小摂動実験は、次の値を使用します。

~~~text
ε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1
~~~

これらはすべて0–255スケールの値です。新しい数値結果はColab再実行後に追記します。

## データセット

[Kaggle Brain Tumor MRI Dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset)を使用します。

| Split | glioma | meningioma | notumor | pituitary | 合計 |
|---|---:|---:|---:|---:|---:|
| Training | 1,400 | 1,400 | 1,400 | 1,400 | 5,600 |
| Testing | 400 | 400 | 400 | 400 | 1,600 |

データセット本体は容量が大きいためGit管理から除外しています。ローカルでは次の構成です。

~~~text
dataset/brain-tumor-mri-dataset/
├── Training/
│   ├── glioma/
│   ├── meningioma/
│   ├── notumor/
│   └── pituitary/
└── Testing/
    ├── glioma/
    ├── meningioma/
    ├── notumor/
    └── pituitary/
~~~

NotebookはColab上で次のZIPを展開する構成です。

~~~text
/content/drive/MyDrive/ThammasatResearch/dataset/archive.zip
~~~

展開先：

~~~text
/content/brain_tumor/
~~~

## モデルと実行環境

- Google Colab
- 保存済み実行時のTensorFlow：**2.20.0**
- GPU：NVIDIA T4
- 入力サイズ：224 × 224 × 3
- バッチサイズ：32
- 乱数シード：42
- Backbone：ImageNet事前学習済みMobileNetV2
- Backboneは凍結
- Optimizer：Adam（learning rate 0.001）
- Loss：Sparse Categorical Crossentropy
- 最大epoch：10

依存パッケージはrequirements.txtにまとめています。TensorFlow 2.20.0のみ保存済み出力から確認できたため固定し、その他の正確なバージョンは未記録です。

ベストモデルの保存先：

~~~text
/content/drive/MyDrive/ThammasatResearch/models/baseline_mobilenetv2.keras
~~~

モデルファイルはGitHubには保存していません。新しいColabセッションではGoogle Driveをマウントして読み込むか、Notebookを再学習してください。

## Colabでの再開手順

1. このNotebookをGoogle Colabで開く。
2. GPUランタイムを有効にする。
3. Google Driveをマウントする。
4. archive.zipと保存済みモデルのパスを確認する。
5. データ作成セルまで上から順番に実行する。
6. 保存済みモデルを読み込む。
7. 通常テスト評価を再現する。
8. 詳細分類評価セルを実行し、ベースラインを再確認する。
9. FGSMセクションを実行し、ε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1を評価する。
10. `fgsm_fine_*.csv/png`の結果をNotebookと資料へ反映する。

## FGSM実験の共通条件

現在のモデルは、入力として画素値0–255の画像を受け取り、モデル内部でmobilenet_v2.preprocess_inputを適用します。したがって、元画像に直接FGSMを適用する場合はεも0–255スケールで扱います。

微小摂動の再実験：

~~~text
ε = 0, 0.01, 0.05, 0.1, 0.25, 0.5, 1
~~~

敵対的画像は次の形で作成し、0–255にクリップします。

~~~text
x_adv = clip(x + ε × sign(∇x loss), 0, 255)
~~~

評価する値：

- Clean Accuracy
- Adversarial Accuracy
- Accuracy Drop
- Attack Success Rate
- クラス別Precision、Recall、F1-score
- 混同行列

Attack Success Rateは「攻撃前に正しく分類された画像のうち、FGSM後に誤分類になった割合」と定義します。

## 再現性に関する注意

- 学習、検証、テストでクラス順を一致させる。
- FGSMはまずuntargeted white-box attackとして実装する。
- εの数値と入力スケールを必ず一緒に報告する。
- 元画像、摂動、敵対的画像を保存して視覚的にも確認する。
- Kaggleデータセットの患者単位の重複情報は未確認であり、データリーケージの可能性を研究上の制約として扱う。
