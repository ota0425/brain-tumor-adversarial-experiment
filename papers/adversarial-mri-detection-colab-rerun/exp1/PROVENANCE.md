# PROVENANCE — exp1 data files

The primary CSV and JSON files in this directory were replaced on
2026-09-08 with the agreed Google Colab rerun results. The pipeline used
a Tesla T4 GPU, TensorFlow 2.20.0, seed 42, and the hash-guarded stage
scripts in `ThammasatResearch/rerun/`. The student and supervisor ran
the pipeline independently and obtained the same reported evaluation
metrics. The student's source artifacts are stored in
`MyDrive/ThammasatResearch/{models,results}`; the supervisor's executed
Colab notebook is retained separately as replication evidence.

The current classifier achieved 0.819375 clean test accuracy
(1,311/1,600). The deployment-calibrated threshold was
0.32068297266960144 and achieved a clean evaluation FPR of 0.1075.
Serialized `.keras` file hashes need not be byte-identical because their
containers may include save-time metadata; downstream stages within
each run nevertheless verified their own manifest chain.

สคริปต์ที่สร้างไฟล์เหล่านี้: `ThammasatResearch/rerun/` ใน repo นี้
(stage 01–06b) — ทุก stage ตรวจ SHA-256 ของโมเดลเทียบ manifest ก่อนรัน

| ไฟล์ | stage ที่สร้าง |
|---|---|
| manifest.json | 01/03/03b (สะสม; รวม entries v2 + v2b ตามรายงาน stage 4 และ 4b) |
| fgsm_summary.csv | 02 |
| detector_v2b_threshold.json | 03b |
| detector_v2b_test_by_epsilon.csv | 04b (Training-side calibration — แสดง FPR ล้มเหลว) |
| deployment_calibration_threshold.json | 05 |
| detector_v2b_deploycal_eval_by_epsilon.csv | 05 |
| pgd_eval_by_epsilon.csv | 06 |
| attack_intersection_analysis.csv | 06b |

The main tables and regenerated figures in `paper.tex` use this Colab
result set. The older RTX 3070 result set remains preserved in the
source archives and the original paper directory.

หมายเหตุตัวเลขนอกไฟล์ที่อ้างใน paper: สถิติ score-shift (validation clean
p90=0.1507/p95=0.4225 vs test p90=0.3550/p95=0.6492; FPR ที่ threshold
เดียวกัน validation 0.0982 vs test 0.1363) มาจาก diagnostic
`diag_score_shift.py` — output อยู่ในเครื่อง GPU [NEEDS: คัดลอก
diag output เป็นไฟล์ในโฟลเดอร์นี้ก่อน submit]

## เพิ่มเติม 2026-09-02 (dataset audit)

ผลตรวจชุด integrity บนเครื่อง GPU (ยังไม่ได้คัดลอก CSV มา — [NEEDS: copy
ก่อน submit]): `results/{text_banner_scan, pixel_leakage_scan,
duplicate_verification, shortcut_check, exclusion_no_aug}.csv` และสคริปต์
`scripts/rerun/{scan_text_banners, check_aug_leakage, verify_duplicates,
pixel_leakage_scan, exclusion_and_shortcut}.py`
ตัวเลข audit ใน paper (Table 6, duplication 100/400, glioma 15.1%/74.4%,
exclusion robustness) มาจากรายงาน relay ของรันเหล่านี้
คำเตือนสำคัญที่บันทึกไว้: perceptual hash 64-bit ใช้กับ MRI slice ไม่ได้
(false alarm สูงมาก) — ตัวเลข duplication ต้องมาจาก pixel_leakage_scan
เท่านั้น

## รูปตัวอย่าง MRI (Fig ใน paper)

`fgsm_perclass_compact.jpg` (239,740 B, sha256 c58436f6…b9e) และ
`pgd40_perclass_compact.jpg` (233,884 B, sha256 e183a799…f32f) — สร้างบน
เครื่อง GPU จาก classifier_seed42 (hash ตรวจก่อน render), exemplar คัด
จาก pool ภาพสะอาด (ไม่ติด banner / ไม่ synthetic / ไม่ duplicate),
บีบเป็น JPEG q75 775×1500 เพื่อส่งข้ามเครื่อง — sha256 ยืนยันตรงต้นทาง
ต้นฉบับ 300dpi PNG + vector PDF ยังอยู่ที่เครื่อง GPU
`results/figures/` — [NEEDS: ใช้ต้นฉบับความละเอียดเต็มตอน camera-ready]
สคริปต์: scripts/rerun/make_example_figure.py, รายละเอียด exemplar ใน
figure_provenance.json (ฝั่ง GPU)

## อัปเดตรูป (2026-09-02, หลัง M6)

ต้นฉบับ vector ถูกนำเข้าแล้ว: `fgsm_examples_eps0.5_perclass.pdf`
(sha256 5e33a415…2bb6) และ `pgd40_examples_eps0.5_perclass.pdf`
(sha256 30635457…372f) — user ถ่ายโอนจากเครื่อง GPU ด้วยตนเอง,
ตรวจเนื้อหาตรงกับชุด exemplar สะอาดสุดท้าย (figure_provenance.json ฝั่ง
GPU) แล้วใช้แทน JPEG compact ใน paper — ประเด็น [NEEDS: full-res ตอน
camera-ready] ปิดแล้ว (ไฟล์ JPEG compact เก็บไว้เป็นหลักฐานการถ่ายโอน)
