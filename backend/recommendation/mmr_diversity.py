"""
Stage 3: Maximal Marginal Relevance (MMR) Diversity & Re-Ranking Engine.
Prevents redundant echo chambers by balancing multi-objective relevance against inter-item similarity.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from backend.schemas.recommendation import CandidateItem


def _item_similarity(item_a: CandidateItem, item_b: CandidateItem) -> float:
    """Computes semantic & category similarity between two candidate items."""
    # 1. Category exact match
    cat_sim = 1.0 if item_a.category.lower() == item_b.category.lower() else 0.0

    # 2. Tag Jaccard overlap
    tags_a = {t.lower() for t in item_a.tags}
    tags_b = {t.lower() for t in item_b.tags}
    tag_overlap = len(tags_a.intersection(tags_b)) / (len(tags_a.union(tags_b)) or 1)

    # 3. Dense Embedding cosine similarity if available
    embed_sim = 0.0
    if item_a.embedding and item_b.embedding and len(item_a.embedding) == len(item_b.embedding):
        dot = sum(a * b for a, b in zip(item_a.embedding, item_b.embedding))
        norm_a = math.sqrt(sum(a * a for a in item_a.embedding))
        norm_b = math.sqrt(sum(b * b for b in item_b.embedding))
        if norm_a > 0 and norm_b > 0:
            embed_sim = max(0.0, dot / (norm_a * norm_b))

    return (0.4 * cat_sim) + (0.3 * tag_overlap) + (0.3 * embed_sim)


class MMRDiversityReRanker:
    """
    Maximal Marginal Relevance (MMR) Re-Ranking:
    Greedily selects items that maximize relevance while minimizing redundancy with already selected items.
    """

    def __init__(self, max_items_per_category: int = 2):
        self.max_items_per_category = max_items_per_category

    def rerank(
        self,
        scored_candidates: List[Tuple[CandidateItem, float, float, float, float]],
        top_k: int = 5,
        diversity_lambda: float = 0.70
    ) -> List[Tuple[CandidateItem, float, float, float, float, float]]:
        """
        Executes MMR re-ranking algorithm.
        Returns: List of tuples (candidate, eff_score, safe_score, adh_score, composite_score, mmr_penalty)
        """
        if not scored_candidates:
            return []

        remaining = list(scored_candidates)
        selected: List[Tuple[CandidateItem, float, float, float, float, float]] = []
        category_counts: Dict[str, int] = {}

        # 1. Select the top candidate unconditionally
        first_item = remaining.pop(0)
        selected.append((first_item[0], first_item[1], first_item[2], first_item[3], first_item[4], 0.0))
        category_counts[first_item[0].category] = 1

        # 2. Greedily select next items based on MMR score
        while remaining and len(selected) < top_k:
            best_idx = -1
            best_mmr_score = -float("inf")
            best_penalty = 0.0

            for idx, item in enumerate(remaining):
                cand, eff, safe, adh, comp = item
                cat = cand.category

                # Category quota constraint
                if category_counts.get(cat, 0) >= self.max_items_per_category:
                    continue

                # Compute maximum similarity to any already selected item
                max_sim = max(
                    _item_similarity(cand, sel[0]) for sel in selected
                )

                # MMR Formulation: lambda * Relevance - (1 - lambda) * MaxSim
                mmr_val = (diversity_lambda * comp) - ((1.0 - diversity_lambda) * max_sim)

                if mmr_val > best_mmr_score:
                    best_mmr_score = mmr_val
                    best_idx = idx
                    best_penalty = (1.0 - diversity_lambda) * max_sim

            if best_idx == -1:
                # If all remaining hit category caps, relax cap and take next highest composite
                item = remaining.pop(0)
                selected.append((item[0], item[1], item[2], item[3], item[4], 0.0))
            else:
                chosen = remaining.pop(best_idx)
                selected.append((chosen[0], chosen[1], chosen[2], chosen[3], chosen[4], best_penalty))
                category_counts[chosen[0].category] = category_counts.get(chosen[0].category, 0) + 1

        return selected
