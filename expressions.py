"""
Árbol de expresiones lógicas para antecedentes de reglas CF.

Permite componer Evidence / NOT / AND / OR de forma extensible (ETC)
sin acoplar el motor a una forma fija de regla.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Sequence

from certainty import cf_and, cf_not, cf_or, validate_cf


class Expression(ABC):
    """Nodo de expresión evaluable bajo un mapa de CE por evidencia."""

    @abstractmethod
    def evaluate(self, evidence_cfs: Mapping[str, float]) -> float:
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class EvidenceRef(Expression):
    """Referencia a una evidencia atómica (p. ej. E1)."""

    code: str

    def evaluate(self, evidence_cfs: Mapping[str, float]) -> float:
        if self.code not in evidence_cfs:
            raise KeyError(f"Evidencia desconocida en el mapa de CE: {self.code}")
        return validate_cf(evidence_cfs[self.code], f"CE({self.code})")

    def describe(self) -> str:
        return self.code


@dataclass(frozen=True)
class Not(Expression):
    """Negación lógica bajo incertidumbre: CF(¬A) = −CF(A)."""

    operand: Expression

    def evaluate(self, evidence_cfs: Mapping[str, float]) -> float:
        return cf_not(self.operand.evaluate(evidence_cfs))

    def describe(self) -> str:
        return f"NOT {self.operand.describe()}"


@dataclass(frozen=True)
class And(Expression):
    """Conjunción: CF = min de los operandos."""

    operands: tuple[Expression, ...]

    def __init__(self, *operands: Expression):
        if len(operands) < 2:
            raise ValueError("AND requiere al menos dos operandos")
        object.__setattr__(self, "operands", tuple(operands))

    def evaluate(self, evidence_cfs: Mapping[str, float]) -> float:
        return cf_and(*(op.evaluate(evidence_cfs) for op in self.operands))

    def describe(self) -> str:
        return " AND ".join(op.describe() for op in self.operands)


@dataclass(frozen=True)
class Or(Expression):
    """Disyunción: CF = max de los operandos."""

    operands: tuple[Expression, ...]

    def __init__(self, *operands: Expression):
        if len(operands) < 2:
            raise ValueError("OR requiere al menos dos operandos")
        object.__setattr__(self, "operands", tuple(operands))

    def evaluate(self, evidence_cfs: Mapping[str, float]) -> float:
        return cf_or(*(op.evaluate(evidence_cfs) for op in self.operands))

    def describe(self) -> str:
        return " OR ".join(op.describe() for op in self.operands)


def E(code: str) -> EvidenceRef:
    """Atajo de construcción: E('E1')."""
    return EvidenceRef(code)


def collect_evidence_codes(expr: Expression) -> Sequence[str]:
    """Extrae códigos de evidencia referenciados (útil para validación)."""
    # Duck typing: evita fallos de isinstance tras reload de módulos.
    code = getattr(expr, "code", None)
    if isinstance(code, str) and not hasattr(expr, "operand") and not hasattr(expr, "operands"):
        return (code,)
    if hasattr(expr, "operand"):
        return collect_evidence_codes(expr.operand)
    if hasattr(expr, "operands"):
        codes: list[str] = []
        for op in expr.operands:
            codes.extend(collect_evidence_codes(op))
        return tuple(dict.fromkeys(codes))
    raise TypeError(f"Expresión no soportada: {type(expr)!r}")
