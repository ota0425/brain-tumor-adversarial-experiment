"""Stage 6b: apples-to-apples detection comparison across attack families.

Stage 6's FGSM-vs-PGD detection comparison had different denominators: PGD
breaks more images, and the extra successes are marginal cases whose weaker
perturbations plausibly give weaker detector signals. This stage measures
that directly instead of leaving it as a plausible explanation:

- For each epsilon, compute per-image success masks and detector scores for
  FGSM, PGD10, and PGD40 in ONE run (persisted to attack_scores.npz so any
  future analysis needs no GPU re-run).
- On the eval-1200 subset, report detection rates restricted to
  (a) the intersection (images broken by both attacks) — the fair set,
  (b) each attack's exclusive successes — the marginal cases that test the
      dilution hypothesis.

Note: PGD uses a random start, and this run's RNG stream order differs from
stage 6's, so raw success counts may differ slightly from stage 6's table.
All comparisons here are within-run, so conclusions are unaffected.
"""
import json
from importlib import import_module

import numpy as np
import pandas as pd
import tensorflow as tf

import common

d3 = import_module("03_detector_v2")
d3b = import_module("03b_detector_v2_calibrated")
d5 = import_module("05_deployment_calibration")
d6 = import_module("06_pgd_eval")

RESULTS_PATH = common.RESULTS_DIR / "attack_intersection_analysis.csv"
SCORES_PATH = common.RESULTS_DIR / "attack_scores.npz"


def main():
    common.set_determinism()
    _, _, test_ds, _ = common.make_datasets()
    classifier = common.load_classifier_verified(
        test_ds.prefetch(tf.data.AUTOTUNE))

    manifest = common.load_manifest()
    actual = common.sha256_of(d3b.DETECTOR_PATH)
    assert actual == manifest["detector_v2b_sha256"]
    cal = json.loads(d5.THRESHOLD_PATH.read_text(encoding="utf-8"))
    assert cal["detector_sha256"] == actual
    threshold = cal["threshold"]
    detector = tf.keras.models.load_model(d3b.DETECTOR_PATH)

    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)

    rng = np.random.default_rng(common.SEED)
    perm = rng.permutation(1600)
    eval_idx = np.sort(perm[d5.CALIB_SIZE:])

    attacks = ("fgsm", "pgd10", "pgd40")
    store = {}  # persisted arrays

    def detector_scores(adv):
        return detector.predict(extract(adv).numpy(), batch_size=256,
                                verbose=0).reshape(-1)

    clean_correct_all = []
    for images, labels in test_ds:
        probs = classifier(images, training=False).numpy()
        clean_correct_all.append(
            np.argmax(probs, axis=1) == labels.numpy().reshape(-1))
    clean_correct = np.concatenate(clean_correct_all)
    store["clean_correct"] = clean_correct
    store["eval_idx"] = eval_idx

    for eps in common.ALL_EPSILONS:
        pgd10 = d6.make_pgd_fn(classifier, float(eps), float(eps) / 4.0, 10)
        pgd40 = d6.make_pgd_fn(classifier, float(eps), float(eps) / 4.0, 40)
        per_attack = {a: {"success": [], "scores": []} for a in attacks}
        for images, labels in test_ds:
            labels_np = labels.numpy().reshape(-1)
            batch_correct = (
                np.argmax(classifier(images, training=False).numpy(),
                          axis=1) == labels_np)
            _, signed = common.compute_fgsm_direction(classifier, images,
                                                      labels)
            adv_by_attack = {
                "fgsm": common.create_adversarial_images(images, signed, eps),
                "pgd10": pgd10(images, labels),
                "pgd40": pgd40(images, labels),
            }
            for name, adv in adv_by_attack.items():
                max_pert = float(tf.reduce_max(
                    tf.abs(adv - tf.cast(images, tf.float32))))
                assert max_pert <= eps + 1e-4, (name, eps, max_pert)
                adv_classes = np.argmax(
                    classifier(adv, training=False).numpy(), axis=1)
                per_attack[name]["success"].append(
                    batch_correct & (adv_classes != labels_np))
                per_attack[name]["scores"].append(detector_scores(adv))
        for name in attacks:
            store[f"{name}_success_eps{eps}"] = np.concatenate(
                per_attack[name]["success"])
            store[f"{name}_scores_eps{eps}"] = np.concatenate(
                per_attack[name]["scores"])
        print(f"eps={eps}: attacks generated and scored")

    np.savez_compressed(SCORES_PATH, **store)

    def det_rate(scores, mask):
        return float(np.mean(scores[mask] >= threshold)) if mask.any() else np.nan

    rows = []
    for eps in common.ALL_EPSILONS:
        f_succ = store[f"fgsm_success_eps{eps}"][eval_idx]
        f_scores = store[f"fgsm_scores_eps{eps}"][eval_idx]
        for pgd_name in ("pgd10", "pgd40"):
            p_succ = store[f"{pgd_name}_success_eps{eps}"][eval_idx]
            p_scores = store[f"{pgd_name}_scores_eps{eps}"][eval_idx]
            both = f_succ & p_succ
            fgsm_only = f_succ & ~p_succ
            pgd_only = p_succ & ~f_succ
            rows.append({
                "epsilon": eps,
                "pair": f"fgsm_vs_{pgd_name}",
                "n_fgsm_success": int(f_succ.sum()),
                "n_pgd_success": int(p_succ.sum()),
                "n_intersection": int(both.sum()),
                "n_fgsm_only": int(fgsm_only.sum()),
                "n_pgd_only": int(pgd_only.sum()),
                "det_fgsm_all": det_rate(f_scores, f_succ),
                "det_pgd_all": det_rate(p_scores, p_succ),
                "det_fgsm_on_intersection": det_rate(f_scores, both),
                "det_pgd_on_intersection": det_rate(p_scores, both),
                "det_fgsm_on_fgsm_only": det_rate(f_scores, fgsm_only),
                "det_pgd_on_pgd_only": det_rate(p_scores, pgd_only),
                "threshold": threshold,
            })
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_PATH, index=False)
    print(df.round(4).to_string(index=False))
    print("saved:", RESULTS_PATH, "and", SCORES_PATH)


if __name__ == "__main__":
    main()
