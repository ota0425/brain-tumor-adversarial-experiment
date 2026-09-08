# NOVELTY — adversarial-mri-detection (PAPER SPRINT M3)

*ค้นจริง 2026-09-02 ผ่าน web search 5 query (medical adversarial detection,
cross-attack generalization, FPR calibration, successful-only detection,
Ma et al. medical detectability) — ลิงก์ทุกอันเปิดตรวจแล้วหรือมาจากผลค้นจริง
ห้ามเพิ่มอ้างอิงที่ไม่ได้ verify*

## 5 papers ที่ใกล้ที่สุด

### 1. Xu, Evans, Qi — "Feature Squeezing: Detecting Adversarial Examples in DNNs" (NDSS 2018)
https://arxiv.org/abs/1704.01155
งานแม่แบบของ consistency-based detection: เทียบ prediction ก่อน/หลัง
squeeze (bit-depth, blur) แล้ว threshold ค่า L1 difference โดยเลือก
threshold จากภาพ clean ให้ได้ FPR เป้าหมาย
**ต่างจากเรา**: (ก) เขา threshold ค่า difference ดิบ เราเรียน detector
บน features+consistency (ข) positive ของเราคือ successful attack เท่านั้น
(ค) เขาเลือก threshold จาก clean เหมือนกัน แต่**ไม่เคยวัดว่า threshold
นั้น transfer ข้าม collection หรือไม่** — ช่องที่เราวัดแล้วพบว่าพัง +3.6 จุด
(ง) โดเมน natural images ไม่ใช่ MRI

### 2. Ma et al. — "Understanding Adversarial Attacks on DL-based Medical Image Analysis Systems" (Pattern Recognition 2021)
https://arxiv.org/abs/1907.10456
ผลคลาสสิกของวงการ: adversarial examples บนภาพแพทย์ (X-ray, fundoscopy,
dermoscopy) **ตรวจจับง่าย** — detector ง่าย ๆ ได้ AUC > 98%
**ต่างจากเรา**: เขารายงาน AUC (threshold-free) เป็นหลัก — ของเรา AUC ก็
~0.99 เหมือนกัน แต่เราแสดงว่า**ช่องว่างระหว่าง AUC สวย ๆ กับ operating
point ที่ใช้จริงคือจุดที่ deployment พัง** (FPR หลุดเป้า +3.6 จุดแม้
AUC ไม่สะเทือน) + successful-only + MRI เนื้องอกสมอง ซึ่งไม่อยู่ใน
modality ของเขา

### 3. "A multi-layered defense against adversarial attacks in brain tumor classification using ensemble adversarial training and feature squeezing" (Scientific Reports 2025)
https://www.nature.com/articles/s41598-025-00890-x
โดเมนเดียวกันเป๊ะ: Kaggle composite brain-tumor MRI 4 คลาส (7,023 ภาพ —
ตระกูลเดียวกับ dataset เรา), VGG16, FGSM+PGD
**ต่างจากเรา**: เป็น **robustness** (adversarial training + squeezing ใน
input pipeline, ได้ accuracy คืน 47–54%) ไม่ใช่ **detection** — ไม่มี
detector, ไม่มี FPR, ไม่มี calibration, ไม่มี cross-attack ฝั่งตรวจจับ
เป็นคู่เทียบเชิง complementary ที่ดี (cite แล้ววางเราเป็นอีกชั้นของ
defense-in-depth บนโจทย์เดียวกัน)

### 4. AED-PADA — "Improving Generalizability of Adversarial Example Detection via Principal Adversarial Domain Adaptation" (2024)
https://arxiv.org/abs/2404.12635
โจมตีปัญหา cross-attack generalization ของ detector ตรง ๆ ด้วย domain
adaptation จากหลาย attack family ต้นทาง
**ต่างจากเรา**: เขาต้องใช้หลาย attack ตอนเทรน — เราแสดงว่าในโดเมนนี้
เทรนจาก FGSM family เดียวก็ transfer ไป PGD ได้อยู่แล้ว (±1 จุดที่
threshold ตรึงไว้) และเขาไม่แตะเรื่อง operating-point/FPR transfer เลย

### 5. "DFT-Based Adversarial Attack Detection in MRI Brain Imaging" (Alzheimer's, 2024)
https://arxiv.org/abs/2408.08489
Detection บน MRI สมองเหมือนกัน (Alzheimer) ใช้ฟีเจอร์เชิงความถี่ (DFT)
**ต่างจากเรา**: positive class คือ adversarial ทั้งหมด (ไม่ใช่
successful-only), ไม่มี pinned-FPR evaluation, ไม่มี cross-collection
calibration story, คนละ task (Alzheimer vs เนื้องอก 4 คลาส)

*(เกี่ยวข้องรอง: "Detecting Adversarial Examples" arXiv 2410.17442 —
layer-prediction-error detector, ไม่แตะ FPR/medical; วรรณกรรม
clean-quantile thresholding ในสาย OOD/prompt-injection 2025–26 ใช้
threshold จาก clean แต่บน distribution เดียวกัน ไม่ได้วัด cross-collection
transfer บนภาพแพทย์)*

## การปรับ claim จากหลักฐาน prior art (สำคัญ — เปลี่ยนจากที่คุยกันก่อน M3)

**Cross-attack generalization (H2) โดยตัวมันเอง "ไม่ใหม่"** — วรรณกรรม
vision ทั่วไปรายงานซ้ำหลายชิ้นว่า detector ที่เทรนจาก FGSM จับ PGD ได้ดี
ดังนั้น**ห้ามชูเป็น contribution หลัก** ให้เป็นหลักฐานความแข็งแรงประกอบ
(และของเราแม่นกว่าตรงวัดที่ threshold ตรึงจริง + intersection analysis)

**มุมที่ยังว่างจริง** (ไม่มีชิ้นไหนใน 5 ตัวรวมกันครบ):
1. วัด **FPR transfer failure ข้าม collection** บน dataset แพทย์จริง
   (+2.9/+3.6 จุด ขณะ AUC นิ่ง) — ชี้ว่าตัวเลข detection ที่วงการรายงาน
   ที่ "FPR ≤ x%" มองโลกดีเกินจริงอย่างเป็นระบบ
2. **Clean-only deployment calibration** 400 ภาพ ตรึง FPR ได้ −0.2 จุด —
   protocol ที่โรงพยาบาลทำได้จริง (ไม่มี labelled attack)
3. **Successful-attack-only** เป็น positive class บน MRI + รายงานทุกอย่าง
   ที่ operating point เดียวที่ตรึงแล้ว (รวม cross-attack)

## Verdict: **incremental แบบมีมุมชัด**

ส่วนผสมแต่ละชิ้นมีที่มา (consistency features → Xu; detectability บนภาพ
แพทย์ → Ma; cross-attack → AED-PADA และอื่น ๆ) แต่แกนเรื่อง
"operating point ไม่ transfer แม้ AUC สวย และ clean-only calibration
ราคาถูกแก้ได้ — วัดจริงบน brain-tumor MRI พร้อม audit trail ทุกตัวเลข"
ยังไม่มีใครทำ paper ต้อง**นำด้วยเรื่อง calibration/deployment** ไม่ใช่
ตัว detector

## GATE-1: PASS (incremental with clear angle)

เงื่อนไขที่ผูกไว้กับ PASS นี้: draft ต้องจัดโครงตามมุมข้อ 1–3 ข้างบน —
ถ้าเขียนแบบ "เรามี detector ใหม่บน MRI" จะชน Ma et al. + DFT paper
ทันทีและกลายเป็น taken
