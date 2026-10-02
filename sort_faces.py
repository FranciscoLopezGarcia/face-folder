#!/usr/bin/env python3
"""Agrupa fotos por persona sin modificar los archivos originales."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import warnings
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import HDBSCAN


IMG_EXT = {".jpg", ".jpeg", ".png"}
RAW_EXT = {".cr2", ".cr3", ".nef", ".arw", ".raf", ".dng"}
SUPPORTED_EXT = IMG_EXT | RAW_EXT

MAX_SIDE = 2000
MIN_PREVIEW_PX = 1200
MIN_FACE_PX = 50
MIN_DET_SCORE = 0.60
MIN_SHARPNESS = 20.0
MIN_SIM_TO_CENTER = 0.50
MIN_CLUSTER_SIZE = 3


def ensure_models():
    """Carga SCRFD + ArcFace de buffalo_l y descarga el paquete si falta."""
    warnings.filterwarnings(
        "ignore",
        message="`estimate` is deprecated.*",
        category=FutureWarning,
        module="insightface.utils.face_align",
    )
    from insightface.app import FaceAnalysis

    model_root = Path(
        os.environ.get("ORDENAR_FOTOS_MODELOS", "~/.insightface")
    ).expanduser()
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"],
        allowed_modules=["detection", "recognition"],
        root=str(model_root),
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))
    return app, None


def is_result_dir(name: str) -> bool:
    """Indica si un nombre corresponde a una salida creada por el programa."""
    if name == "resultado":
        return True
    prefix = "resultado_"
    return name.startswith(prefix) and name[len(prefix) :].isdigit()


def find_photos(root: Path, _out_names=None) -> list[Path]:
    """Encuentra fotos y excluye carpetas ocultas y resultados anteriores."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") or is_result_dir(part) for part in relative_parts):
            continue
        if path.suffix.lower() in SUPPORTED_EXT:
            files.append(path)
    return sorted(files)


def load_image(path: Path):
    """Devuelve una imagen BGR reducida, o None si el formato no pudo leerse."""
    if path.suffix.lower() in RAW_EXT:
        import rawpy

        with rawpy.imread(str(path)) as raw:
            try:
                thumb = raw.extract_thumb()
                if thumb.format == rawpy.ThumbFormat.JPEG:
                    img = cv2.imdecode(
                        np.frombuffer(thumb.data, np.uint8), cv2.IMREAD_COLOR
                    )
                else:
                    img = cv2.cvtColor(thumb.data, cv2.COLOR_RGB2BGR)
            except Exception:
                img = None
            if img is None or max(img.shape[:2]) < MIN_PREVIEW_PX:
                img = cv2.cvtColor(
                    raw.postprocess(half_size=True), cv2.COLOR_RGB2BGR
                )
    else:
        img = cv2.imdecode(
            np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR
        )

    if img is None:
        return None
    height, width = img.shape[:2]
    scale = MAX_SIDE / max(height, width)
    if scale < 1:
        img = cv2.resize(
            img,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    return img


def analyze(photos, app, _unused=None):
    """Extrae embeddings y calidad; un fallo individual no detiene el lote."""
    embeddings, owners, quality = [], [], []
    no_face, failed = set(), []
    print(f"Fotos encontradas: {len(photos)}\n")

    for index, path in enumerate(photos, 1):
        try:
            img = load_image(path)
            if img is None:
                raise ValueError("no se pudo leer la imagen")
            faces = app.get(img)
            if not faces:
                no_face.add(index - 1)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if faces else None
            for face in faces:
                x1, y1, x2, y2 = (max(int(value), 0) for value in face.bbox)
                crop = (
                    cv2.resize(gray[y1:y2, x1:x2], (112, 112))
                    if x2 > x1 and y2 > y1
                    else None
                )
                sharpness = (
                    cv2.Laplacian(crop, cv2.CV_64F).var()
                    if crop is not None
                    else 0.0
                )
                embeddings.append(face.normed_embedding.astype(np.float32))
                owners.append(index - 1)
                quality.append(
                    (min(x2 - x1, y2 - y1), float(face.det_score), sharpness)
                )
        except Exception as exc:
            failed.append(index - 1)
            print(f"  ! {path.name}: {exc}")

        if index % 25 == 0 or index == len(photos):
            print(
                f"\rAnalizando {index}/{len(photos)} | "
                f"Caras detectadas: {len(embeddings)}",
                end="",
                flush=True,
            )

    print("\n")
    return (
        np.array(embeddings, dtype=np.float32).reshape(-1, 512),
        np.array(owners),
        np.array(quality, dtype=np.float64).reshape(-1, 3),
        no_face,
        failed,
    )


def cluster(embeddings, quality):
    """Devuelve una etiqueta por cara; -1 significa revisión manual."""
    labels = np.full(len(embeddings), -1)
    good = (
        (quality[:, 0] >= MIN_FACE_PX)
        & (quality[:, 1] >= MIN_DET_SCORE)
        & (quality[:, 2] >= MIN_SHARPNESS)
    )
    good_indices = np.where(good)[0]
    if len(good_indices) < MIN_CLUSTER_SIZE:
        return labels

    subset_labels = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=2,
        metric="euclidean",
        copy=True,
    ).fit_predict(embeddings[good_indices])
    labels[good_indices] = subset_labels

    for label in set(subset_labels) - {-1}:
        members = np.where(labels == label)[0]
        center = embeddings[members].mean(axis=0)
        center /= np.linalg.norm(center) + 1e-9
        labels[members[embeddings[members] @ center < MIN_SIM_TO_CENTER]] = -1
    return labels


def copy_unique(src: Path, destination: Path, used: set) -> Path:
    """Copia sin sobrescribir; si un nombre existe, agrega un sufijo numérico."""
    destination.mkdir(parents=True, exist_ok=True)
    name, counter = src.name, 1
    while (destination / name).exists() or (destination, name) in used:
        name = f"{src.stem}_{counter}{src.suffix}"
        counter += 1
    used.add((destination, name))
    target = destination / name
    shutil.copy2(src, target)
    return target


def next_output_dir(base: Path) -> Path:
    output = base / "resultado"
    counter = 2
    while output.exists():
        output = base / f"resultado_{counter}"
        counter += 1
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Detecta y agrupa personas en fotos locales. Los originales nunca se "
            "mueven, borran ni modifican: sólo se copian a una carpeta resultado."
        ),
        epilog=(
            "Ejemplos:\n"
            "  python sort_faces.py evento\n"
            "  python sort_faces.py evento D:\\Clasificadas\n"
            "  python sort_faces.py --download-models"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "photos",
        nargs="?",
        type=Path,
        help="carpeta que contiene las fotos",
    )
    parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        help="carpeta donde crear resultado (por defecto: la carpeta de fotos)",
    )
    parser.add_argument(
        "--download-models",
        action="store_true",
        help="descarga y verifica que buffalo_l pueda cargarse, sin analizar fotos",
    )
    return parser


def run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.download_models:
        print("Preparando el modelo facial buffalo_l...")
        try:
            ensure_models()
        except Exception as exc:
            print(f"Error al preparar el modelo: {exc}", file=sys.stderr)
            return 1
        print("Modelo preparado. Las próximas ejecuciones pueden funcionar offline.")
        return 0

    if args.photos is None:
        parser.error("falta la carpeta de fotos")

    root = args.photos.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"la carpeta de fotos no existe o no es accesible: {root}")
    if is_result_dir(root.name):
        parser.error(
            "la carpeta indicada parece una salida anterior; selecciona la carpeta "
            "original de fotos"
        )

    base = (
        args.destination.expanduser().resolve()
        if args.destination is not None
        else root
    )
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(
            f"No se puede crear o usar la carpeta de destino '{base}': {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        photos = find_photos(root)
    except OSError as exc:
        print(f"No se pudo recorrer la carpeta de fotos '{root}': {exc}", file=sys.stderr)
        return 1
    if base != root and root in base.parents:
        photos = [photo for photo in photos if base not in photo.parents]
    if not photos:
        print(
            "No se encontraron fotos compatibles. Usa --help para ver los formatos.",
            file=sys.stderr,
        )
        return 1

    print("Cargando el modelo facial (la primera vez puede descargar archivos)...")
    try:
        app, _ = ensure_models()
    except Exception as exc:
        print(
            "No se pudo cargar el modelo facial. Revisa la conexión durante la "
            f"primera ejecución y vuelve a intentar. Detalle: {exc}",
            file=sys.stderr,
        )
        return 1

    embeddings, owners, quality, no_face, failed = analyze(photos, app)

    print("Agrupando caras...")
    labels = cluster(embeddings, quality) if len(embeddings) else np.array([], int)
    person_ids = sorted(set(labels.tolist()) - {-1})
    person_ids.sort(key=lambda label: -len(set(owners[labels == label])))
    print(f"Personas agrupadas: {len(person_ids)}\n")

    destinations: dict[int, set[str]] = {}
    for label, owner in zip(labels, owners):
        folder = (
            "revision"
            if label == -1
            else f"atleta_{person_ids.index(label) + 1:03d}"
        )
        destinations.setdefault(int(owner), set()).add(folder)
    for owner in no_face | set(failed):
        destinations.setdefault(owner, set()).add("revision")

    output = next_output_dir(base)
    print("Copiando resultados...")
    used: set = set()
    copy_errors = 0
    for owner, folders in destinations.items():
        for folder in sorted(folders):
            try:
                copy_unique(photos[owner], output / folder, used)
            except OSError as exc:
                copy_errors += 1
                print(f"  ! No se pudo copiar {photos[owner]}: {exc}")

    review_count = sum(
        "revision" in folders for folders in destinations.values()
    )
    print(f"Fotos en revisión: {review_count}")
    print(f"Sin cara o ilegibles: {len(no_face) + len(failed)}")
    print(f"Resultado: {output}")
    if copy_errors:
        print(
            f"Finalizó con {copy_errors} error(es) de copia. Revisa los mensajes anteriores.",
            file=sys.stderr,
        )
        return 1
    print("Listo.")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    return run(parser.parse_args(argv), parser)


if __name__ == "__main__":
    raise SystemExit(main())
