"""Genera banco_prueba/ con imágenes LFW para desarrollo local."""

import random
import shutil
from pathlib import Path

import cv2
import numpy as np
from sklearn.datasets import fetch_lfw_people, get_data_home


N_TARGETS, PER_PERSON, N_DISTRACTORS = 50, 5, 200
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT = PROJECT_ROOT / "banco_prueba"


def lfw_dir():
    directory = Path(get_data_home()) / "lfw_home" / "lfw_funneled"
    if not directory.is_dir():
        print("Descargando LFW (sólo para desarrollo, ~230 MB)...")
        fetch_lfw_people(min_faces_per_person=70, download_if_missing=True)
    return directory


def save_jpg(src, dst):
    image = cv2.imdecode(np.fromfile(str(src), np.uint8), cv2.IMREAD_COLOR)
    cv2.imwrite(str(dst), image, [cv2.IMWRITE_JPEG_QUALITY, 95])


def main():
    people = {
        directory.name: sorted(directory.glob("*.jpg"))
        for directory in lfw_dir().iterdir()
        if directory.is_dir()
    }
    randomizer = random.Random(42)
    targets = randomizer.sample(
        [name for name, files in people.items() if len(files) >= 5], N_TARGETS
    )
    distractors = randomizer.sample(
        [name for name, files in people.items() if len(files) == 1], N_DISTRACTORS
    )

    photos = []
    for name in targets:
        photos += [
            (name, file) for file in randomizer.sample(people[name], PER_PERSON)
        ]
    photos += [(name, people[name][0]) for name in distractors]
    randomizer.shuffle(photos)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "evento").mkdir(parents=True)
    for index, (name, src) in enumerate(photos, 1):
        filename = f"IMG_{index:04d}.jpg"
        save_jpg(src, OUT / "evento" / filename)
        (OUT / "verdad" / name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT / "evento" / filename, OUT / "verdad" / name / filename)

    print(f"Fotos totales:     {len(photos)}")
    print(f"Personas objetivo: {len(targets)} ({PER_PERSON} fotos cada una)")
    print(f"Distractores:      {len(distractors)} (1 foto cada uno)")
    print(f"Ruta generada:     {OUT}")


if __name__ == "__main__":
    main()
