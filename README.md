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
| 混同行列・Precision・Recall・F1-score | コード修正済み、Colabで再実行が必要 |
| FGSM実装 | 未着手 |
| ε別の攻撃評価 | 未着手 |
| Adversarial Training | 第二段階 |

確認済みのベースライン結果：

- Validation Accuracy（最高）：**0.91071**（epoch 9）
- Test Loss：**0.5203**
- Test Accuracy：**0.8319（83.19%）**
- テスト画像数：1,600枚

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
8. 詳細分類評価セルを実行し、混同行列とクラス別指標を保存する。
9. FGSMを実装し、ε別に評価する。

## FGSM実験の共通条件

現在のモデルは、入力として画素値0–255の画像を受け取り、モデル内部でmobilenet_v2.preprocess_inputを適用します。したがって、元画像に直接FGSMを適用する場合はεも0–255スケールで扱います。

初期候補：

~~~text
ε = 0, 1, 2, 4, 8
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
