# REVIEW SYNTHESIS — M6 (panel of 3, adversarial) — 2026-09-02

## คะแนน

| กรรมการ | คะแนน | เงื่อนไข |
|---|---|---|
| Paradigm Guardian | **6/10** (4 ถ้าไม่แก้) | แก้ near-tautology framing ของ contribution 2 + statistical resolution |
| Adversarial ML (defense-evaluation) | **6/10** (3 ถ้าไม่แก้) | ทุก claim ประสิทธิผลต้อง qualified "non-adaptive"; footnote หน่วย ε |
| Medical Imaging (clinical) | **5/10 → 6 เมื่อแก้** | threat motivation + testbed status + budget illustrative + calibration assumption |

**GATE-3: คะแนนต่ำสุด (หลังแก้ FIX-NOW ซึ่งใส่ครบแล้ว) = 6 ≥ 5 → PASS → verdict เสนอ: `queued`**

## จุดที่ panel เห็นตรงกัน

- **ของแข็ง**: audit ที่หา defect ของ dataset ตัวเองแล้วแสดงว่าข้อสรุปรอด
  (FPR *ดีขึ้น* ใต้ exclusion), inverted-leakage result ที่รายงานสวน
  สมมติฐานตัวเอง, intersection protocol, hash-chain artifact trail,
  strict dominance (FGSM ⊂ PGD) ที่ scope ถูกต้อง
- **ของอ่อน**: ไม่มี interval estimate ทั้งเล่ม (สองกรรมการทักตรงกัน —
  จุดอ่อนที่จริงที่สุดของ draft), dataset เดียว/backbone เดียว,
  ไม่มี adaptive attack (ยอมรับได้เพราะเป็น measurement paper แต่ต้อง
  ไม่มีประโยคที่ quote เป็น security claim ได้)

## FIX-NOW — ใส่ครบแล้วทั้ง 10 จุด, recompile ผ่าน (10 หน้าพอดี)

1. Contribution 2 reframe: deployment calibration = standard practice,
   contribution คือ measurement (−0.2 vs +3.6, 400 ภาพ clean พอ) (Guardian)
2. ย่อหน้า resolution ก่อน Table 5: binomial half-width ±1pt (n≈900) /
   ±7pt (n=138), หลักฐานคือ sign consistency บน paired comparisons;
   crossover ลดระดับเป็น "consistent sign pattern suggesting" (Guardian+AdvML)
3. Footnote เทียบเซ็ต 70.3% (eval-1200) vs 81.6% (full test @13.6% FPR) (Guardian)
4. Caption Tables 3/4/5: แถว ε=0.01 ต่ำกว่า 8-bit quantization —
   completeness only (Guardian+AdvML)
5. Conclusion: "effective **against the non-adaptive attacks evaluated
   here**" + ประโยคปิดว่า adaptive ยังเป็นคำถามเปิด (AdvML)
6. Footnote หน่วย: ε=1 (0–255) = 1/255 ≈ 0.0039 normalized (AdvML)
7. Threat motivation ใน intro + cite Finlayson et al. Science 2019 (Medical)
8. ประโยค testbed: classifier ไม่ใช่ clinical tool (Medical)
9. Scoping: 10% budget เป็น illustrative + calibration set assumed
   attack-free / ต้อง controlled & auditable (Medical)
10. หนึ่งประโยค moral ของ glioma-banner collapse (subpopulation failure
    ใต้ aggregate accuracy ที่ดูดี) (Medical)

## RUN-LATER (ไม่ block GATE-3 — ลิสต์ไว้ให้ตัดสินใจ)

- **McNemar paired test** FGSM vs PGD บน intersection จาก
  attack_scores.npz — ยืนยัน crossover เป็น finding เต็มตัว (ไม่ใช้ GPU,
  ~นาทีเดียวบนเครื่อง GPU machine)
- **Stage 6c perturbation norms** — ปิดกลไก crossover (GPU ~20 นาที)
- Adaptive attack (Carlini-style) — future work ประกาศแล้วใน paper

## FIX-BEFORE-SUBMIT (งานมนุษย์ → SUBMISSION_TODO ใน M7)

- ชื่อนักศึกษา / สังกัด / อีเมล (ตอนนี้ [NEEDS] 3 จุดบนหน้าแรก)
- Dataset citation + ระบุ constituent sources ของ composite (Medical
  referee ยืนยัน: ไม่ optional สำหรับ venue นี้)
- [VERIFY] author lists: SciRep 2025, AED-PADA, DFT-MRI
- สลับรูป Fig 1 เป็นต้นฉบับ full-res จากเครื่อง GPU ตอน camera-ready
- คัดลอก audit CSVs จากเครื่อง GPU เข้า exp1/ (byte-diff ยืนยัน)
