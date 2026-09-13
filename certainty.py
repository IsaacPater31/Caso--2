"""
Operaciones matemáticas de la Teoría de Factores de Certeza (CF).

Responsabilidad única: razonamiento numérico bajo incertidumbre.
Sin conocimiento de dominio (evidencias, reglas ni hipótesis).
"""

from __future__ import annotations

from typing import Iterable


CF_MIN = -1.0
CF_MAX = 1.0
_EPS = 1e-12


def clamp_cf(value: float) -> float:
    """Restringe un CF al intervalo cerrado [-1, 1]."""
    return max(CF_MIN, min(CF_MAX, value))


def validate_cf(value: float, name: str = "CF") -> float:
    """Valida y normaliza un Factor de Certeza."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} debe ser numérico, recibido: {type(value).__name__}")
    cf = float(value)
    if cf < CF_MIN - _EPS or cf > CF_MAX + _EPS:
        raise ValueError(f"{name}={cf} fuera de rango [{CF_MIN}, {CF_MAX}]")
    return clamp_cf(cf)


def cf_not(cf: float) -> float:
    """Negación: CF(¬A) = −CF(A)."""
    return clamp_cf(-validate_cf(cf))


def cf_and(*cfs: float) -> float:
    """Conjunción: CF(A ∧ B ∧ …) = min(CF(A), CF(B), …)."""
    if not cfs:
        raise ValueError("cf_and requiere al menos un operando")
    return min(validate_cf(c) for c in cfs)


def cf_or(*cfs: float) -> float:
    """Disyunción: CF(A ∨ B ∨ …) = max(CF(A), CF(B), …)."""
    if not cfs:
        raise ValueError("cf_or requiere al menos un operando")
    return max(validate_cf(c) for c in cfs)


def propagate(cf_antecedent: float, cf_rule: float) -> float:
    """
    Propagación antecedente → consecuente.

    CF(H, E) = CF(E) × CR  si CF(E) > 0;  en caso contrario la regla
    no aporta evidencia (aporte 0). Un CF negativo en el antecedente
    indica certeza de que la premisa NO se cumple.
    """
    ce = validate_cf(cf_antecedent, "CF(antecedente)")
    cr = validate_cf(cf_rule, "CR")
    if ce <= 0.0:
        return 0.0
    return clamp_cf(ce * cr)


def combine(cf1: float, cf2: float) -> float:
    """
    Co-suscripción (combinación acumulativa) de dos aportes a la misma hipótesis.

    - Ambos > 0:  CF1 + CF2 − CF1·CF2
    - Ambos < 0:  CF1 + CF2 + CF1·CF2
    - Signos opuestos / cero: (CF1 + CF2) / (1 − min(|CF1|, |CF2|))
    """
    a = validate_cf(cf1, "CF1")
    b = validate_cf(cf2, "CF2")

    if abs(a) < _EPS:
        return b
    if abs(b) < _EPS:
        return a

    if a > 0.0 and b > 0.0:
        return clamp_cf(a + b - a * b)
    if a < 0.0 and b < 0.0:
        return clamp_cf(a + b + a * b)

    denominator = 1.0 - min(abs(a), abs(b))
    if abs(denominator) < _EPS:
        return clamp_cf(1.0 if (a + b) > 0 else -1.0)
    return clamp_cf((a + b) / denominator)


def combine_many(cfs: Iterable[float]) -> float:
    """Reduce una secuencia de aportes con la fórmula acumulativa estándar."""
    total = 0.0
    for cf in cfs:
        total = combine(total, cf)
    return total
