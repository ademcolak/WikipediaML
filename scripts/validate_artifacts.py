#!/usr/bin/env python3
"""
Artifact Validator for WikipediaML
Checks compatibility between graph, embeddings, and training data artifacts.
"""

import argparse
import json
import pickle
import random
import sys
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.sparse import load_npz


def load_pickle(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_graph_embeddings(
    graph_dir: Path,
    embeddings_dir: Path,
    sample_size: int = 20
) -> Tuple[List[str], List[str], Dict]:
    errors: List[str] = []
    warnings: List[str] = []

    mapping_file = graph_dir / "page_mappings.pkl"
    if not mapping_file.exists():
        errors.append(f"Missing graph mapping: {mapping_file}")
        return errors, warnings, {}

    mappings = load_pickle(mapping_file)
    graph_pages = len(mappings.get("pages", {}))

    stats_file = graph_dir / "graph_statistics.json"
    graph_stats = load_json(stats_file) if stats_file.exists() else {}
    graph_fingerprint = mappings.get("pages_fingerprint") or graph_stats.get("pages_fingerprint")

    embeddings_file = embeddings_dir / "embeddings.npy"
    if not embeddings_file.exists():
        errors.append(f"Missing embeddings: {embeddings_file}")
        return errors, warnings, mappings

    embeddings_shape = np.load(embeddings_file, mmap_mode="r").shape
    if embeddings_shape[0] != graph_pages:
        errors.append(
            f"Embeddings rows ({embeddings_shape[0]:,}) != graph pages ({graph_pages:,})"
        )

    meta_file = embeddings_dir / "embedding_metadata.pkl"
    if not meta_file.exists():
        warnings.append(f"Missing embedding metadata: {meta_file}")
    else:
        meta = load_pickle(meta_file)
        meta_pages = meta.get("n_pages")
        if meta_pages is not None and meta_pages != graph_pages:
            errors.append(f"Metadata n_pages ({meta_pages:,}) != graph pages ({graph_pages:,})")

        meta_fingerprint = meta.get("pages_fingerprint")
        if graph_fingerprint and meta_fingerprint and graph_fingerprint != meta_fingerprint:
            errors.append("Pages fingerprint mismatch between graph and embeddings")

        meta_index_to_page_id = meta.get("index_to_page_id")
        graph_index_to_page_id = mappings.get("index_to_page_id")
        if meta_index_to_page_id and graph_index_to_page_id:
            n = min(len(meta_index_to_page_id), len(graph_index_to_page_id))
            if n > 0:
                sample_size = min(sample_size, n)
                idxs = random.sample(range(n), sample_size)
                mismatch = sum(
                    1 for i in idxs
                    if meta_index_to_page_id[i] != graph_index_to_page_id[i]
                )
                if mismatch > 0:
                    errors.append(f"Mapping mismatch in sample: {mismatch}/{sample_size}")

    matrix_file = graph_dir / "adjacency_matrix.npz"
    if matrix_file.exists():
        matrix_shape = load_npz(matrix_file).shape
        if matrix_shape[0] != graph_pages:
            errors.append(
                f"Adjacency shape ({matrix_shape[0]:,}) != graph pages ({graph_pages:,})"
            )
    else:
        warnings.append(f"Missing adjacency matrix: {matrix_file}")

    return errors, warnings, mappings


def check_training_samples(
    training_dir: Path,
    mappings: Dict,
    sample_size: int = 1000
) -> Tuple[List[str], List[str], List[Dict]]:
    errors: List[str] = []
    warnings: List[str] = []

    samples_file = training_dir / "training_samples.json"
    if not samples_file.exists():
        warnings.append(f"Missing training samples: {samples_file}")
        return errors, warnings, []

    samples = load_json(samples_file)
    if not samples:
        errors.append("Training samples file is empty")
        return errors, warnings, []

    page_id_to_index = mappings.get("page_id_to_index", {})
    sample_size = min(sample_size, len(samples))
    subset = random.sample(samples, sample_size)

    missing_pages = 0
    index_mismatch = 0
    candidate_mismatch = 0

    for s in subset:
        start_id = s.get("start_page_id")
        target_id = s.get("target_page_id")

        if start_id not in page_id_to_index or target_id not in page_id_to_index:
            missing_pages += 1
            continue

        if "start_idx" in s and page_id_to_index.get(start_id) != s.get("start_idx"):
            index_mismatch += 1
        if "target_idx" in s and page_id_to_index.get(target_id) != s.get("target_idx"):
            index_mismatch += 1

        if "candidate_page_id" in s and "candidate_idx" in s:
            candidate_id = s.get("candidate_page_id")
            if page_id_to_index.get(candidate_id) != s.get("candidate_idx"):
                candidate_mismatch += 1

    if missing_pages > 0:
        errors.append(f"Training samples with missing page IDs: {missing_pages}/{sample_size}")
    if index_mismatch > 0:
        errors.append(f"Training samples index mismatch: {index_mismatch}/{sample_size}")
    if candidate_mismatch > 0:
        errors.append(f"Candidate index mismatch: {candidate_mismatch}/{sample_size}")

    return errors, warnings, samples


def check_sample_paths(
    graph_dir: Path,
    mappings: Dict,
    samples: List[Dict],
    n_samples: int = 10,
    max_depth: int = 4
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not samples:
        warnings.append("No training samples available for path checks")
        return errors, warnings

    matrix_file = graph_dir / "adjacency_matrix.npz"
    if not matrix_file.exists():
        warnings.append(f"Missing adjacency matrix: {matrix_file}")
        return errors, warnings

    adjacency = load_npz(matrix_file)
    page_id_to_index = mappings.get("page_id_to_index", {})

    subset = random.sample(samples, min(n_samples, len(samples)))
    found = 0

    for s in subset:
        start_id = s.get("start_page_id")
        target_id = s.get("target_page_id")
        start_idx = page_id_to_index.get(start_id)
        target_idx = page_id_to_index.get(target_id)
        if start_idx is None or target_idx is None:
            continue

        queue = deque([(start_idx, 0)])
        seen = {start_idx}
        ok = False

        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            neighbors = adjacency[node].indices
            if target_idx in neighbors:
                ok = True
                break
            for n in neighbors:
                if n not in seen:
                    seen.add(n)
                    queue.append((n, depth + 1))

        if ok:
            found += 1

    if found == 0:
        warnings.append(
            f"No paths found within depth {max_depth} in {len(subset)} samples"
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate graph, embeddings, and training artifacts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--graph-dir", type=str, default="data/graph")
    parser.add_argument("--embeddings-dir", type=str, default="data/embeddings")
    parser.add_argument("--training-dir", type=str, default="data/training")
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--check-paths", action="store_true")
    parser.add_argument("--path-samples", type=int, default=10)
    parser.add_argument("--path-max-depth", type=int, default=4)
    args = parser.parse_args()

    graph_dir = Path(args.graph_dir)
    embeddings_dir = Path(args.embeddings_dir)
    training_dir = Path(args.training_dir)

    all_errors: List[str] = []
    all_warnings: List[str] = []

    errors, warnings, mappings = check_graph_embeddings(
        graph_dir, embeddings_dir
    )
    all_errors.extend(errors)
    all_warnings.extend(warnings)

    errors, warnings, samples = check_training_samples(
        training_dir, mappings, sample_size=args.sample_size
    )
    all_errors.extend(errors)
    all_warnings.extend(warnings)

    if args.check_paths:
        errors, warnings = check_sample_paths(
            graph_dir,
            mappings,
            samples,
            n_samples=args.path_samples,
            max_depth=args.path_max_depth
        )
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    print("\n" + "=" * 80)
    print("Artifact Validation Report")
    print("=" * 80)

    if all_errors:
        print("\n❌ Errors:")
        for e in all_errors:
            print(f"- {e}")

    if all_warnings:
        print("\n⚠️  Warnings:")
        for w in all_warnings:
            print(f"- {w}")

    if not all_errors and not all_warnings:
        print("\n✓ All checks passed")

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
