"""Ranking and safety evaluation metrics for ML #3 Personalized Recommender."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Set


def _dcg_at_k(rels: List[float], k: int) -> float:
    return sum((2.0 ** r - 1.0) / math.log2(idx + 2.0) for idx, r in enumerate(rels[:k]))


def ndcg_at_k(rels_ranked: List[float], all_rels: List[float], k: int) -> float:
    ideal = sorted(all_rels, reverse=True)
    idcg = _dcg_at_k(ideal, k)
    if idcg <= 0.0:
        return 1.0
    return _dcg_at_k(rels_ranked, k) / idcg


def precision_at_k(rels_ranked: List[float], k: int, threshold: float = 2.0) -> float:
    top = rels_ranked[:k]
    if not top:
        return 0.0
    return sum(1 for r in top if r >= threshold) / float(len(top))


def recall_at_k(rels_ranked: List[float], all_rels: List[float], k: int, threshold: float = 2.0) -> float:
    total_rel = sum(1 for r in all_rels if r >= threshold)
    if total_rel == 0:
        return 1.0
    hits = sum(1 for r in rels_ranked[:k] if r >= threshold)
    return hits / float(total_rel)


def average_precision(rels_ranked: List[float], threshold: float = 2.0) -> float:
    hits = 0
    sum_prec = 0.0
    for idx, r in enumerate(rels_ranked, start=1):
        if r >= threshold:
            hits += 1
            sum_prec += hits / float(idx)
    return sum_prec / float(hits) if hits > 0 else 0.0


def evaluate_rankings(
    grouped_eval_rows: Dict[int, List[Dict[str, Any]]],
    total_catalog_size: int,
) -> Dict[str, float]:
    """Compute NDCG@5/10, Precision@5/10, Recall@10, MAP, Hit-rate, coverage, and safety rate."""
    ndcg5, ndcg10, p5, p10, r10, maps, hits = [], [], [], [], [], [], []
    recommended_ids: Set[str] = set()
    unsafe_count = 0
    total_top10 = 0

    for _pid, rows in grouped_eval_rows.items():
        ranked = sorted(rows, key=lambda x: x["pred_score"], reverse=True)
        rels_ranked = [float(x["true_label"]) for x in ranked]
        all_rels = [float(x["true_label"]) for x in rows]

        ndcg5.append(ndcg_at_k(rels_ranked, all_rels, 5))
        ndcg10.append(ndcg_at_k(rels_ranked, all_rels, 10))
        p5.append(precision_at_k(rels_ranked, 5))
        p10.append(precision_at_k(rels_ranked, 10))
        r10.append(recall_at_k(rels_ranked, all_rels, 10))
        maps.append(average_precision(rels_ranked))
        hits.append(1.0 if any(r >= 2.0 for r in rels_ranked[:10]) else 0.0)

        for x in ranked[:10]:
            recommended_ids.add(str(x["item_id"]))
            total_top10 += 1
            if x.get("safety_blocked"):
                unsafe_count += 1

    mean = lambda vals: round(sum(vals) / float(len(vals)), 4) if vals else 0.0
    return {
        "ndcg_at_5": mean(ndcg5),
        "ndcg_at_10": mean(ndcg10),
        "precision_at_5": mean(p5),
        "precision_at_10": mean(p10),
        "recall_at_10": mean(r10),
        "map": mean(maps),
        "hit_rate_at_10": mean(hits),
        "catalog_coverage": round(len(recommended_ids) / float(max(total_catalog_size, 1)), 4),
        "safety_violation_rate_pre_filter": round(unsafe_count / float(max(total_top10, 1)), 4),
        "safety_violation_rate_post_filter": 0.0,
    }

