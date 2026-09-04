# 論文提出・再実行計画（2026-09-04）

## 現在の最優先事項

- 論文提出期限は **2026-09-15**。MICAD公式サイトでは最終論文締切を **2026-09-15 (AoE)** と案内している。
- 論文はMr. Surasakと次のOverleafプロジェクトで共同執筆している。
  - <https://www.overleaf.com/project/6a979075abfd87f25d127c5d>
- 直近の作業は、新しい実験を追加することより先に、先生が作成した`rerun`パイプラインを順番に実行し、生成された数値が論文の数値と一致するか確認することである。
- Overleafは認証が必要な共同プロジェクトであるため、このローカル環境から本文は確認できていない。数値照合時はOverleafの表・図または先生から受け取った論文ソースを参照する。

## 先生から受け取った再実行パッケージ

ローカルで確認した実体は次の場所にある。

~~~text
ThammasatResearch/
├── Adversarial MRI Rerun.pdf
├── Rerun pipeline — student run guide.pdf
└── ThammasatResearch/
    ├── dataset/archive.zip
    ├── models/
    ├── results/
    └── rerun/
~~~

`rerun`内のPython群は、従来の3つのNotebookを機能単位に分け、再現性と監査可能性を追加した論文用パイプラインである。従来Notebookは研究経過を示す履歴として残すが、今後の論文数値の一次生成元にはしない。

ガイドには`~/ThammasatResearch/scripts/rerun`とあるが、現在受領したフォルダの実体は`ThammasatResearch/ThammasatResearch/rerun`であり、`scripts`ディレクトリは存在しない。実行時は`TR_BASE`を内側の`ThammasatResearch`へ明示的に設定する。

## 旧結果が置き換えられた理由

先生の`Adversarial MRI Rerun.pdf`による監査結果は次のとおり。

1. 2026-08-23の元モデルはclean test accuracy 83.19%（1,331/1,600）だった。
2. `baseline_mobilenetv2.keras`が2026-09-01に再学習され、78.13%（1,250/1,600）の別モデルで上書きされた。
3. 実験2の再開処理は検知器の再学習と閾値選択をスキップした一方、最終テストだけを新しい分類器で再実行した。
4. そのため、以前の実験2テスト表は旧検知器・旧閾値と新分類器の特徴を混在させた **mixed-era artifact** であり、論文の最終結果として使用できない。
5. seedと決定論的演算を固定したclean rerunの基準値は **81.875%（1,310/1,600）** である。今後はこの再実行結果を基準とする。

これは検知手法そのものの失敗ではなく、artifact管理の問題である。以前の83.19%および78.13%の結果は研究履歴として保持するが、現行論文の主結果と混ぜない。

## パイプラインの保護機構

- seedは42で固定し、`tf.keras.utils.set_random_seed`とTensorFlowの決定論的演算を使用する。
- データセットZIPのSHA-256を検証する。完全な期待値は`common.py`にあり、末尾は`fdb4`である。
- 学習したモデルのSHA-256とclean accuracyを`results/manifest.json`へ記録する。
- 下流stageはモデルhashとmanifestを照合し、不一致なら処理を停止する。
- 学習stageは既存のcanonical modelを自動上書きしない。`--force`は下流結果をすべて無効化するため、通常は使用しない。
- 古い`models/baseline_mobilenetv2.keras`を、新しい`models/classifier_seed42.keras`へ名前変更またはコピーして流用しない。

## 実行前に確認した状態

2026-09-04のread-only確認結果：

- `dataset/archive.zip`は158 MBで、SHA-256は`882817250048c78ef7a759cf23e540d7b581f2327b16663c9d3db12f5d2ffdb4`。`common.py`の期待値と一致した。
- `rerun/SHA256SUMS`に登録された8本の監査scriptは、すべて`sha256sum -c`を通過した。
- 現在のWSL既定環境はPython 3.12.3だが、TensorFlowは未導入である。実行前にガイドどおりTensorFlow 2.20系を含む専用venvを作る必要がある。

受領直後のローカルパッケージには、再実行で作成される次のcanonical artifactがまだない。

- `models/classifier_seed42.keras`
- `results/manifest.json`
- `results/deployment_calibration_threshold.json`
- `results/pgd_eval_by_epsilon.csv`
- `results/attack_intersection_analysis.csv`

したがって、古い保存結果の途中からではなくStage 1から新しい一連のrerunを開始する。ガイドが参照する`papers/adversarial-mri-detection/`、`PROVENANCE.md`、`review-synthesis.md`、`make_figures.py`も現在の受領フォルダには含まれていない。論文との完全な機械的照合や図の再生成に必要なら、先生またはOverleafから取得する。

## 実行順序

環境はガイドに合わせ、Python 3.12、TensorFlow 2.20系、GPUを使用する。GPUの有無は理論上の評価値を意図的に変える条件ではないが、決定論的設定と依存バージョンを固定し、実行環境を記録する。

| Stage | Script | 目的 |
|---:|---|---|
| 1 | `01_train_classifier.py` | 決定論的なMobileNetV2分類器を学習しmanifestを作る |
| 2 | `02_fgsm_sweep.py` | Test setでFGSMのepsilon sweepを行う |
| 3 | `03_detector_v2.py` | full validationで閾値を選ぶconsistency detectorを学習する |
| 4 | `04_final_test_v2.py` | detector v2の最終テストを行う |
| 5 | `03b_detector_v2_calibrated.py` | model selection用val_Aと閾値用val_Bを分離してv2bを学習する |
| 6 | `04b_final_test_v2b.py` | validation由来の閾値がTestingへ移らない問題を確認する |
| 7 | `05_deployment_calibration.py` | Testingをclean calibration 400枚とevaluation 1,200枚に分けて閾値を固定する |
| 8 | `06_pgd_eval.py` | 固定閾値でPGD K=10/40を評価する |
| 9 | `06b_intersection_analysis.py` | FGSM/PGD双方の成功集合の共通部分で検知率を公平に比較する |

想定チェックポイント：

- Stage 1 clean test accuracy: **0.81875（1,310/1,600）**
- Stage 7 deployment threshold: **約0.3612**
- Stage 7 evaluation FPR: **約0.0983**
- Stage 8–9: 共通成功集合上のPGD検知率はFGSMとの差が概ね1 percentage point以内

最初のチェックポイントが一致しない場合は、先へ進まず、データhash、TensorFlow/CUDA、seed、ログ、モデルhashを調べる。

## 論文へ照合する主結果

clean rerunで報告された分類器の値：

| 指標 | Clean rerun |
|---|---:|
| Clean test accuracy | 81.875%（1,310/1,600） |
| Attack success rate at epsilon=0.5 | 88.8% |
| Attack success rate at epsilon=1.0 | 95.0% |

Testing domainのclean画像400枚だけで閾値をcalibrationし、残り1,200枚で評価した結果：

| epsilon（0–255） | 学習時の扱い | Successful-attack detection | ROC-AUC | PR-AUC |
|---:|---|---:|---:|---:|
| 0.01 | known | 54.2% | 0.887 | 0.080 |
| 0.05 | unseen | 70.3% | 0.923 | 0.535 |
| 0.10 | known | 87.6% | 0.962 | 0.858 |
| 0.25 | unseen | 97.9% | 0.988 | 0.979 |
| 0.50 | known | 99.0% | 0.995 | 0.993 |
| 1.00 | unseen | 98.7% | 0.995 | 0.994 |

主な解釈は、検知器の順位性能は未知epsilonにも汎化するが、Training/Validation collectionで決めた判定閾値はTesting collectionへ完全には移らない、というものである。Testing domainのclean画像400枚で閾値を校正すると、evaluation FPRを9.83%へ戻せる。epsilon=0.01はpositiveが少なくPR-AUC 0.080であり、「微小攻撃も十分検知できた」とは主張しない。

## データ品質監査で残すべき事項

- `scan_text_banners.py`はburned-in text/bannerを調べ、gliomaのcollection shiftを評価する。
- `pixel_leakage_scan.py`が正しい重複検査であり、meningioma Testing 400枚中100枚のTraining重複を報告している。
- `check_aug_leakage.py`の93.9% near-duplicateという結果は、MRIに対する64-bit perceptual hashの誤検知で **反証済み**。監査履歴として残されているが、その数値を論文で使用しない。
- `verify_duplicates.py`、`exclusion_and_shortcut.py`、`clean_fpr_exclusion.py`は、前段のartifactがそろった後に`rerun`ディレクトリ内から実行する。

## 各Stageの照合記録

各実行について、次を残す。

| Stage | 終了時刻 | 実行環境 | 出力artifact | 期待値 | 実測値 | 差 | 判定 |
|---:|---|---|---|---:|---:|---:|---|
| 1 |  |  |  | 0.81875 |  |  | 未実行 |
| 2 |  |  |  | 論文表と照合 |  |  | 未実行 |
| 3–4 |  |  |  | 論文表と照合 |  |  | 未実行 |
| 5–6 |  |  |  | FPR transfer failure |  |  | 未実行 |
| 7 |  |  |  | threshold≈0.3612, FPR≈0.0983 |  |  | 未実行 |
| 8 |  |  |  | PGD K=10/40 |  |  | 未実行 |
| 9 |  |  |  | FGSMとの差≈1 point以内 |  |  | 未実行 |

CSVは丸める前の値を比較し、表では丸め桁をそろえる。「一致」は完全一致か許容誤差内かを明記する。異なる場合は論文側の数字をその場で書き換えず、原因と使用artifactを確認する。

## 9月15日までの作業目安

- 9月4日：受領物、パス、依存環境、論文の比較対象を固定
- 9月5日：Stage 1–4を実行し、classifier/FGSM/detector v2を照合
- 9月6日：Stage 5–7を実行し、FPR transferとdeployment calibrationを照合
- 9月7–8日：Stage 8–9を実行し、PGDとintersection analysisを照合
- 9月9日：データ品質監査と除外分析を実行
- 9月10日：全CSV、図、manifest、ログを論文と照合し、差分を先生へ報告
- 9月11–12日：Methods、Results、Limitationsを更新
- 9月13日：英語全文と引用を確認し、先生へ最終ドラフトを渡す
- 9月14日：最終修正、PDF、投稿要件、著者情報を確認
- 9月15日：余裕を持って投稿

## 共有と保存の原則

- 論文本文の共同編集はOverleafを正本とする。
- コードの版管理はGitHubを正本とする。
- 大容量データセットとモデルはGitHubへ入れず、アクセス制御された保存先を使う。
- 実行済みNotebookの出力は結果確認には有用だが、第三者の再現にはデータ、モデル、依存環境が別途必要である。
- private Google Driveのデータやモデルへ認証なしで直接アクセスすることはできない。共有相手が再実行する場合は、Drive権限を与えるか、別の安全な配布方法を用意する。

## 参照先

- 現行の再実行手順：`ThammasatResearch/ThammasatResearch/rerun/README.md`
- 監査説明：`ThammasatResearch/Adversarial MRI Rerun.pdf`
- 学生向けガイド：`ThammasatResearch/Rerun pipeline — student run guide.pdf`
- FGSM以前の確定履歴：`docs/meeting_record_2026-09-01.md`
- MICAD: <https://www.micad.org/>
- MICAD submission: <https://www.micad.org/submission.html>
