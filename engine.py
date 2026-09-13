"""
Motor de inferencia por Factores de Certeza.

Orquesta evaluación de antecedentes, propagación y co-suscripción.
No conoce la UI ni los valores por defecto del caso clínico.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from certainty import combine_many, propagate, validate_cf
from knowledge import KnowledgeBase, Rule


@dataclass(frozen=True)
class RuleEvaluation:
    rule: Rule
    cf_antecedent: float
    cf_contribution: float
    activated: bool

    @property
    def status(self) -> str:
        return "ACTIVADA" if self.activated else "DESCARTADA"


@dataclass(frozen=True)
class HypothesisResult:
    code: str
    name: str
    description: str
    cf_final: float
    contributing_rules: tuple[RuleEvaluation, ...]


@dataclass(frozen=True)
class TriageResult:
    evidence_cfs: Mapping[str, float]
    rule_evaluations: tuple[RuleEvaluation, ...]
    hypotheses: tuple[HypothesisResult, ...]
    ranked: tuple[HypothesisResult, ...]
    primary: HypothesisResult | None
    explanation: str = ""

    @property
    def diagnosis_code(self) -> str | None:
        return self.primary.code if self.primary else None


@dataclass
class CertaintyFactorEngine:
    """Motor parametrizable: recibe una KB y evalúa cualquier vector de CE."""

    knowledge_base: KnowledgeBase
    activation_threshold: float = 0.0

    def __post_init__(self):
        self.knowledge_base.validate()

    def evaluate(self, evidence_cfs: Mapping[str, float]) -> TriageResult:
        normalized = self._normalize_evidence(evidence_cfs)
        rule_evals = tuple(
            self._evaluate_rule(rule, normalized) for rule in self.knowledge_base.rules
        )
        hypotheses = tuple(
            self._resolve_hypothesis(h.code, rule_evals)
            for h in self.knowledge_base.hypotheses
        )
        ranked = tuple(
            sorted(hypotheses, key=lambda h: h.cf_final, reverse=True)
        )
        primary = self._select_primary(ranked)
        return TriageResult(
            evidence_cfs=normalized,
            rule_evaluations=rule_evals,
            hypotheses=hypotheses,
            ranked=ranked,
            primary=primary,
            explanation=self._build_explanation(primary, ranked),
        )

    def _normalize_evidence(self, evidence_cfs: Mapping[str, float]) -> dict[str, float]:
        known = self.knowledge_base.evidence_by_code()
        missing = set(known) - set(evidence_cfs)
        if missing:
            raise KeyError(f"Faltan factores de certeza para: {sorted(missing)}")
        unknown = set(evidence_cfs) - set(known)
        if unknown:
            raise KeyError(f"Evidencias no declaradas en la KB: {sorted(unknown)}")
        return {code: validate_cf(cf, f"CE({code})") for code, cf in evidence_cfs.items()}

    def _evaluate_rule(
        self, rule: Rule, evidence_cfs: Mapping[str, float]
    ) -> RuleEvaluation:
        cf_ant = rule.antecedent.evaluate(evidence_cfs)
        contribution = propagate(cf_ant, rule.cf_rule)
        activated = cf_ant > self.activation_threshold
        return RuleEvaluation(
            rule=rule,
            cf_antecedent=cf_ant,
            cf_contribution=contribution if activated else 0.0,
            activated=activated,
        )

    def _resolve_hypothesis(
        self, hypothesis_code: str, rule_evals: tuple[RuleEvaluation, ...]
    ) -> HypothesisResult:
        hypo = self.knowledge_base.hypothesis_by_code()[hypothesis_code]
        contributors = tuple(
            re for re in rule_evals if re.rule.consequent == hypothesis_code
        )
        active_cfs = [re.cf_contribution for re in contributors if re.activated]
        cf_final = combine_many(active_cfs) if active_cfs else 0.0
        return HypothesisResult(
            code=hypo.code,
            name=hypo.name,
            description=hypo.description,
            cf_final=cf_final,
            contributing_rules=contributors,
        )

    @staticmethod
    def _select_primary(ranked: tuple[HypothesisResult, ...]) -> HypothesisResult | None:
        if not ranked:
            return None
        top = ranked[0]
        if top.cf_final <= 0.0:
            return None
        return top

    @staticmethod
    def _build_explanation(
        primary: HypothesisResult | None,
        ranked: tuple[HypothesisResult, ...],
    ) -> str:
        if primary is None:
            return (
                "Ninguna hipótesis acumula certeza positiva. "
                "Se recomienda revisión manual por el analista SOC."
            )
        order = " > ".join(f"{h.code}({h.cf_final:.4f})" for h in ranked)
        return (
            f"Triage prioritario: {primary.code} — {primary.name} "
            f"(CF={primary.cf_final:.4f}). Orden de confianza: {order}."
        )
