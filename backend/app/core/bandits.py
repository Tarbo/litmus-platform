from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class ThompsonPosterior:
    variant_id: str
    variant_name: str
    exposures: int
    conversions: int
    alpha: float
    beta: float

    @property
    def expected_rate(self) -> float:
        return self.alpha / (self.alpha + self.beta)


def build_thompson_posteriors(
    variant_rows: list[tuple[str, str]],
    counts_by_variant: dict[str, tuple[int, int]],
) -> list[ThompsonPosterior]:
    posteriors: list[ThompsonPosterior] = []
    for variant_id, variant_name in variant_rows:
        exposures, conversions = counts_by_variant.get(variant_id, (0, 0))
        failures = max(0, exposures - conversions)
        posteriors.append(
            ThompsonPosterior(
                variant_id=variant_id,
                variant_name=variant_name,
                exposures=exposures,
                conversions=conversions,
                alpha=1.0 + conversions,
                beta=1.0 + failures,
            )
        )
    return posteriors


def choose_variant_thompson(posteriors: list[ThompsonPosterior], rng: random.Random) -> ThompsonPosterior:
    if not posteriors:
        raise ValueError('At least one posterior is required')
    return max(posteriors, key=lambda posterior: rng.betavariate(posterior.alpha, posterior.beta))


def estimate_win_probabilities(
    posteriors: list[ThompsonPosterior],
    rng: random.Random,
    draws: int = 400,
) -> dict[str, float]:
    if not posteriors:
        return {}
    if draws <= 0:
        draws = 1

    wins = {posterior.variant_id: 0 for posterior in posteriors}
    for _ in range(draws):
        winner = max(posteriors, key=lambda posterior: rng.betavariate(posterior.alpha, posterior.beta))
        wins[winner.variant_id] += 1
    return {variant_id: wins[variant_id] / draws for variant_id in wins}
