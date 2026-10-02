"""Evalúa el clustering contra identidades conocidas de LFW."""

import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import sort_faces as sf  # noqa: E402


LFW = Path.home() / "scikit_learn_data" / "lfw_home" / "lfw_funneled"
TEST = PROJECT_ROOT / "lfw_test"
N_PEOPLE, PER_PERSON, N_SINGLES = 80, 8, 150


def build():
    if TEST.exists():
        return
    if not LFW.is_dir():
        raise SystemExit(
            "No se encontró LFW. Ejecuta primero scripts/preparar_banco.py."
        )
    randomizer = random.Random(42)
    people = {
        directory.name: sorted(directory.glob("*.jpg"))
        for directory in LFW.iterdir()
        if directory.is_dir()
    }
    multi = [name for name, files in people.items() if len(files) >= 4]
    single = [name for name, files in people.items() if len(files) == 1]
    TEST.mkdir()
    for name in randomizer.sample(multi, N_PEOPLE):
        for file in randomizer.sample(people[name], min(PER_PERSON, len(people[name]))):
            shutil.copy(file, TEST / f"{name}__{file.name}")
    for name in randomizer.sample(single, N_SINGLES):
        file = people[name][0]
        shutil.copy(file, TEST / f"{name}__{file.name}")


def metrics(truth, labels):
    clustered = labels != -1
    groups = defaultdict(list)
    for identity, label in zip(truth, labels):
        if label != -1:
            groups[label].append(identity)
    true_pairs = false_pairs = 0
    for group in groups.values():
        counts = Counter(group)
        same = sum(value * (value - 1) // 2 for value in counts.values())
        total = len(group) * (len(group) - 1) // 2
        true_pairs += same
        false_pairs += total - same
    identities = Counter(truth)
    real_pairs = sum(value * (value - 1) // 2 for value in identities.values())
    impure = sum(1 for group in groups.values() if len(set(group)) > 1)
    return {
        "caras": len(truth),
        "grupos": len(groups),
        "impuros": impure,
        "a_revision": int((~clustered).sum()),
        "precision_pares": true_pairs / max(true_pairs + false_pairs, 1),
        "recall_pares": true_pairs / max(real_pairs, 1),
        "caras_mal": false_pairs,
    }


def main():
    build()
    photos = sf.find_photos(TEST)
    app, _ = sf.ensure_models()
    embeddings, owners, quality, no_face, _failed = sf.analyze(photos, app)
    truth = np.array([photos[owner].name.split("__")[0] for owner in owners])

    main_faces = np.zeros(len(owners), bool)
    for owner in set(owners):
        indices = np.where(owners == owner)[0]
        main_faces[indices[np.argmax(quality[indices, 0])]] = True
    embeddings = embeddings[main_faces]
    truth = truth[main_faces]
    quality = quality[main_faces]

    print(
        "Calidad (lado/nitidez) percentiles 5,50:",
        np.percentile(quality[:, 0], [5, 50]),
        np.percentile(quality[:, 2], [5, 50]),
    )
    print(f"Identidades reales: {len(set(truth))} | sin cara: {len(no_face)}\n")

    for similarity in (0.35, 0.40, 0.45, 0.50):
        for cluster_size in (2, 3, 4):
            sf.MIN_SIM_TO_CENTER = similarity
            sf.MIN_CLUSTER_SIZE = cluster_size
            result = metrics(truth, sf.cluster(embeddings, quality))
            print(
                f"sim>={similarity:.2f} min_cluster={cluster_size}: "
                f"grupos={result['grupos']:3d} impuros={result['impuros']:2d} "
                f"revision={result['a_revision']:3d}/{result['caras']} "
                f"precision={result['precision_pares']:.4f} "
                f"recall={result['recall_pares']:.3f}"
            )


if __name__ == "__main__":
    main()
