"""
Base de conocimiento del triage SOC (Caso 2).

Responsabilidad única: declarar evidencias, hipótesis y reglas.
El motor de inferencia consume esta base sin conocer el dominio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from certainty import validate_cf
from expressions import And, Expression, Not, Or, E, collect_evidence_codes


@dataclass(frozen=True)
class Evidence:
    code: str
    description: str
    default_cf: float

    def __post_init__(self):
        validate_cf(self.default_cf, f"CE({self.code})")


@dataclass(frozen=True)
class Hypothesis:
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class Rule:
    id: str
    antecedent: Expression
    consequent: str
    cf_rule: float
    description: str = ""

    def __post_init__(self):
        validate_cf(self.cf_rule, f"CR({self.id})")


@dataclass(frozen=True)
class KnowledgeBase:
    evidences: tuple[Evidence, ...]
    hypotheses: tuple[Hypothesis, ...]
    rules: tuple[Rule, ...]

    def evidence_by_code(self) -> Mapping[str, Evidence]:
        return {e.code: e for e in self.evidences}

    def hypothesis_by_code(self) -> Mapping[str, Hypothesis]:
        return {h.code: h for h in self.hypotheses}

    def default_evidence_cfs(self) -> dict[str, float]:
        return {e.code: e.default_cf for e in self.evidences}

    def validate(self) -> None:
        evidence_codes = set(self.evidence_by_code())
        hypothesis_codes = set(self.hypothesis_by_code())

        for rule in self.rules:
            if rule.consequent not in hypothesis_codes:
                raise ValueError(
                    f"Regla {rule.id}: consecuente '{rule.consequent}' no está en la KB"
                )
            for code in collect_evidence_codes(rule.antecedent):
                if code not in evidence_codes:
                    raise ValueError(
                        f"Regla {rule.id}: evidencia '{code}' no está en la KB"
                    )


# ── Dominio Caso 2 ────────────────────────────────────────────

EVIDENCES = (
    Evidence(
        "E1",
        "Pico anómalo extremo en el consumo de ancho de banda entrante.",
        0.85,
    ),
    Evidence(
        "E2",
        "Intentos masivos fallidos de autenticación SSH en puertos de servidores.",
        0.90,
    ),
    Evidence(
        "E3",
        "Alertas del antivirus corporativo local en las terminales (endpoints).",
        -0.40,
    ),
    Evidence(
        "E4",
        "Modificaciones inexplicables en las firmas SHA-256 de archivos del sistema web.",
        0.70,
    ),
)

HYPOTHESES = (
    Hypothesis("CH1", "DDoS", "Ataque de Denegación de Servicio Distribuido (DDoS)"),
    Hypothesis(
        "CH2",
        "Ransomware",
        "Intrusión de Ransomware / Secuestro de Archivos",
    ),
    Hypothesis(
        "CH3",
        "Falsa Alarma",
        "Falsa Alarma (Falso positivo por tráfico legítimo)",
    ),
)

RULES = (
    Rule(
        id="R1",
        antecedent=E("E1"),
        consequent="CH1",
        cf_rule=0.80,
        description="SI Pico de Ancho de Banda (E1) ENTONCES DDoS (CH1)",
    ),
    Rule(
        id="R2",
        antecedent=And(E("E2"), E("E4")),
        consequent="CH2",
        cf_rule=0.75,
        description="SI Intentos fallidos SSH (E2) AND Cambios en Firmas (E4) ENTONCES Ransomware (CH2)",
    ),
    Rule(
        id="R3",
        antecedent=E("E3"),
        consequent="CH2",
        cf_rule=0.60,
        description="SI Antivirus detecta amenazas (E3) ENTONCES Ransomware (CH2)",
    ),
    Rule(
        id="R4",
        antecedent=Or(Not(E("E1")), Not(E("E3"))),
        consequent="CH3",
        cf_rule=0.50,
        description="SI NOT Pico de Ancho de Banda (NOT E1) OR Antivirus Inactivo (NOT E3) ENTONCES Falsa Alarma (CH3)",
    ),
)

DEFAULT_KB = KnowledgeBase(evidences=EVIDENCES, hypotheses=HYPOTHESES, rules=RULES)
DEFAULT_KB.validate()
