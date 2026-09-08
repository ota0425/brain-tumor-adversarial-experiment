# SEED — adversarial-mri-detection (PAPER SPRINT M1)

*ต้นทาง: แบบ (ข) — งานนักศึกษา ThammasatResearch (FGSM attack + detection
บน Brain Tumor MRI, MobileNetV2) ที่ผ่านการ audit + rerun ทั้งสายเมื่อ
2026-09-01/02 บนเครื่อง GPU (RTX 3070, TF 2.20.0, seed 42) ภายใต้
hash-guarded pipeline (`ThammasatResearch/rerun/`) — **การทดลอง decisive
รันเสร็จแล้ว มี artifact ครบ** สถานการณ์กลับด้านจาก sprint ปกติ: หลักฐาน
มาก่อน แล้วจึงตั้งกรอบ paper. M1 เขียนโดย Claude 2026-09-02.*

## คำถามวิจัย (หนึ่งประโยค)

Detector ที่เทรนจากตัวอย่าง FGSM ล้วน ๆ ของ classifier ตัวเดียว และตั้ง
operating point จาก**ภาพ clean ล้วน ๆ** ของโดเมน deployment — สามารถ
ตรวจจับ successful attack จาก **attack family ที่ไม่เคยเห็น (PGD)** บน
MRI เนื้องอกสมอง ที่ false-positive rate ที่**ตรึงไว้ได้จริง** หรือไม่?

## ทำไมน่าสนใจ

1. **ช่องว่างเชิงประเมินผล**: งาน adversarial detection ส่วนใหญ่รายงาน
   ROC-AUC หรือ detection rate ที่ threshold ซึ่ง calibrate จากข้อมูล
   ฝั่งเดียวกับที่เทรน — เราวัดแล้วพบว่าบน dataset จริง (Training/ กับ
   Testing/ เป็นคนละ collection) threshold แบบนั้น**หลุดเป้า FPR
   +2.9 ถึง +3.6 จุดเสมอ** ในขณะที่ AUC ดูดีไม่เปลี่ยน — ตัวเลข
   detection ที่ตีพิมพ์กันจึงมองโลกดีเกินจริงอย่างเป็นระบบ
2. **คำตอบราคาถูก**: ภาพ clean เพียง 400 ภาพจากโดเมน deployment
   (ไม่ต้องมีตัวอย่าง attack แม้แต่ภาพเดียว — ตรงกับสิ่งที่โรงพยาบาลมีจริง)
   ตรึง FPR ได้ −0.2 จุดจากเป้า
3. **Cross-attack transfer เป็นหลักฐานที่แรงกว่า unseen-ε**: perturbation
   ของ FGSM มีลายเซ็นเฉพาะ (±ε ทุกพิกเซล) ถ้า detector จับได้แค่ลายเซ็น
   นี้ ก็ไร้ค่าเชิง defense — การที่มันจับ PGD ได้เท่ากันโดยไม่เคยเห็น
   คือหลักฐานว่าจับสัญญาณทั่วไปของการถูกโจมตี
4. **บริบท medical imaging ยกน้ำหนักทุกข้อ**: ผลบวกลวงมีต้นทุนคลินิก
   ชัดเจน (สแกนซ้ำ/ชะลอการวินิจฉัย) — FPR ที่อ้างได้จริงจึงไม่ใช่
   รายละเอียดเชิงเทคนิคแต่เป็นเงื่อนไขการใช้งาน

## สมมติฐานที่เดาไว้ (และผลที่วัดได้แล้ว)

- **H1 (ยืนยันแล้ว)**: consistency-feature detector (GAP features +
  probabilities + blur-consistency) generalize ข้าม ε ที่ไม่เคยเห็น —
  unseen ε วางบน trend เดียวกับ known ทุกจุด
- **H2 (ยืนยันแล้ว — ผลหลักของ paper)**: generalize ข้าม attack family:
  detection ต่อ PGD (K=10/40, random start) ต่างจาก FGSM ไม่เกิน ±1 จุด
  ทุก ε; ROC-AUC แทบทับกัน (0.887–0.994)
- **H3 (ยืนยันแล้ว — contribution เชิงระเบียบวิธี)**: operating point
  ไม่ transfer ข้าม collection (+2.9/+3.6 จุด) แต่ clean-only deployment
  calibration 400 ภาพแก้ได้ (eval FPR 9.83% ต่อเป้า 10%)
- **H4 (หักล้างแล้ว — stage 6b, 2026-09-02)**: สมมติฐาน dilution ผิด —
  บน intersection (ภาพเดียวกันเป๊ะ) ส่วนต่าง ~1 จุดที่ ε ≥ 0.25 ยังอยู่
  (ของจริง ไม่ใช่ artifact ของตัวหาร) และมี **crossover ที่ ~ε=0.25**:
  ต่ำกว่านั้น PGD ตรวจจับ*ง่ายกว่า* FGSM +2–3 จุด สูงกว่านั้นยากกว่า ~1 จุด
  แถมภาพที่ PGD พังได้เพิ่มที่ ε สูงถูกจับ 98–100% (ตรงข้าม dilution)
  ข้อเท็จจริงใหม่ที่คมสุด: **n_fgsm_only = 0 ทุกแถว — FGSM success set
  เป็น strict subset ของ PGD ทุก ε** (การประเมิน robustness ด้วย FGSM
  อย่างเดียว optimistic โดยพิสูจน์ได้) กลไกที่เสนอ (ยังไม่วัด): FGSM อยู่
  มุม ε-ball เสมอ ส่วน PGD หยุดข้างในเมื่อข้าม boundary แล้ว —
  วัดได้ด้วย perturbation norms บน intersection (stage 6c ถ้าต้องการ)
- **ข้อจำกัดที่ประกาศล่วงหน้า**: ε=0.01 บนสเกล 0–255 เล็กกว่า 1 ระดับ
  quantization ของภาพ 8-bit (FGSM ≡ PGD10 ถึงทศนิยม 4 ตำแหน่ง) — ตัดแถว
  หรือติดหมายเหตุ; และทั้งหมดยังไม่ใช่ adaptive attack ต่อ detector
  (Carlini-style) — ประกาศเป็น future work ตรง ๆ

## Decisive experiment

**รันแล้ว** — stage 6 ของ pipeline: เทรน detector จาก FGSM เท่านั้น
(ε ∈ {0.01, 0.1, 0.5}) ตรึง threshold จาก clean calibration 400 ภาพ
(stage 5) แล้ววัด detection ต่อ successful PGD attack (family ที่ไม่เคย
เห็น) บน eval set 1,200 ภาพเดียวกันแถวต่อแถวกับตาราง FGSM —
ถ้า detection ร่วงแรง = detector จับลายเซ็น FGSM (paper ตาย);
ถ้าเท่ากัน = จับสัญญาณการถูกโจมตีทั่วไป (paper เกิด) **ผล: เท่ากัน (±1 จุด)**

ชิ้นสุดท้ายที่ยังรันอยู่: stage 6b (intersection analysis, H4) — เก็บ
apples-to-apples ก่อน reviewer อ่านส่วนต่าง 1 จุดผิดทาง

**Artifacts** (เครื่อง GPU `~/ThammasatResearch/`): `results/manifest.json`
(SHA-256 chain), `detector_v2b_test_by_epsilon.csv`,
`deployment_calibration_threshold.json`,
`detector_v2b_deploycal_eval_by_epsilon.csv`, `pgd_eval_by_epsilon.csv`,
`attack_intersection_analysis.csv` (รอ), log เต็มทุก stage ใน
`results/_logs/` · สคริปต์: repo `ThammasatResearch/rerun/`
· classifier `3fab6948…` · detector v2b `606a4686…` · threshold 0.3612

## GATE-0: PASS

คำถามชัด (ประโยคเดียว, มีเงื่อนไขวัดได้: unseen family + pinned FPR),
decisive experiment ชัดและ**รันจบแล้วพร้อม artifact ตรวจย้อนได้ทุกตัวเลข**
— เหลือความเสี่ยงเดียวคือ novelty (GATE-1/M3): ต้องเช็ค prior art ฝั่ง
consistency-based detection (feature squeezing — Xu et al.), attack-
transferability ของ detector, และ threshold/conformal calibration ใน
medical imaging ก่อนเขียน draft
