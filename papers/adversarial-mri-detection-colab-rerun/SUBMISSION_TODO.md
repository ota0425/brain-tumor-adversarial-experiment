# SUBMISSION_TODO — adversarial-mri-detection (M7, 2026-09-02)

เป้า: **MICAD 2026** (Edinburgh, 22–24 ต.ค.) · ส่งผ่าน OpenConf
http://www.micad.org/openconf/ · **deadline 15 ก.ย. 2026** (ขยายจาก
25 ส.ค. — เห็นบนหน้า CFP 2 ก.ย.) · single-blind · ≤10 หน้า (ตอนนี้ 10
พอดี — เพิ่มอะไรต้องแลกพื้นที่) · notification ~2 สัปดาห์หลังส่ง ·
registration 29 ก.ย. · proceedings Springer LNEE

## ค้างในไฟล์ ([NEEDS]/[VERIFY] — ห้าม submit ทั้งที่ยังอยู่)

- [ ] **หน้าแรก 3 จุด**: ชื่อนักศึกษา (+ลำดับ author), สังกัด, อีเมล
      (paper.tex บรรทัด \author/\institute)
- [ ] **Dataset citation** (refs.bib `dataset_needs`): ระบุ citation
      จริงของ variant 7,200 ภาพ (5,600/1,600) — **ถามนักศึกษาว่า
      archive.zip มาจากไหน**; composite ตระกูลนี้ (Nickparvar) มาจาก
      figshare + SARTAJ + Br35H และมาตรฐานคือ 7,023 ภาพ — variant เรา
      ต่างจากนั้น ต้องอธิบายที่มาได้ · §3 ควรระบุ constituent sources
      ตามคำขอ referee 3
- [ ] **[VERIFY] author lists 3 รายการ** ใน refs.bib: SciRep 2025
      (s41598-025-00890-x), AED-PADA (2404.12635), DFT-MRI (2408.08489)
      — เปิดหน้า paper จริงคัดชื่อ (ห้ามเดา) · Ma et al. ใส่ชื่อไว้แล้ว
      แต่ยังติด [VERIFY] — เช็คแล้วลบ tag

## Audit trail ต้องปิดก่อนส่ง

- [ ] คัดลอก CSV จากเครื่อง GPU → `exp1/`: text_banner_scan,
      pixel_leakage_scan, duplicate_verification, shortcut_check,
      exclusion_no_aug, clean_fpr_exclusion (+ diag_score_shift output)
- [ ] **byte-diff ทุกไฟล์ใน exp1/ ที่เป็นสำเนา relay** กับต้นฉบับบน
      เครื่อง GPU (`~/ThammasatResearch/results/`) — รายการใน
      exp1/PROVENANCE.md

## เช็คโดยมนุษย์ก่อนส่ง (กฎแล็บ: อาจารย์อ่านทุกบรรทัด)

- [ ] อ่าน paper.pdf ทุกบรรทัด — โดยเฉพาะประโยคที่พูดแทนนักศึกษา
- [ ] Scoop check รอบสุดท้าย: ค้น arXiv ซ้ำด้วย query จาก novelty.md
      (โฟกัส "FPR calibration adversarial detection medical" หลัง
      2026-09) ว่าไม่มีใครตัดหน้า
- [ ] สะกดชื่อ/สังกัดถูกทุกตัวอักษร · อีเมลติดต่อใช้งานได้
- [ ] หน้า submission ระบุ "formatted in WORD and PDF" — เช็คใน
      OpenConf ว่ารับ PDF อย่างเดียวได้ไหม (template LaTeX เป็นทางการ
      อยู่แล้ว น่าจะได้ แต่ยืนยันก่อน)
- [ ] คนไปนำเสนอที่ Edinburgh + ลงทะเบียนภายในกำหนด (เงื่อนไขตีพิมพ์:
      อย่างน้อยหนึ่ง author ลงทะเบียนเต็ม)

## ไม่ block การส่ง แต่ทำได้ถ้ามีเวลา (จาก review-synthesis RUN-LATER)

- [ ] McNemar paired test FGSM vs PGD จาก attack_scores.npz (ไม่ใช้
      GPU, ~1 นาที) — ยกระดับ crossover จาก observation เป็น finding
- [ ] Stage 6c perturbation norms (~20 นาที GPU) — ปิดกลไก crossover
- [ ] Adaptive attack — ประกาศเป็น future work ใน paper แล้ว

## สถานะ gates

GATE-0 PASS (2026-09-02) · GATE-1 PASS incremental-with-angle ·
GATE-2 ผ่านโดยหลักฐาน stage 1–6b + audit (ไม่มี invariant พัง;
dataset defects วัดและเปิดเผยแล้ว) · GATE-3 PASS (panel ต่ำสุด 6/10
หลัง FIX-NOW ครบ 10 จุด) — ดู review-synthesis.md ·
**การกดส่งจริงเป็นการตัดสินใจของมนุษย์เท่านั้น**
