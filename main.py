"""
Interfaz de operador SOC — Sistema Experto de Triage por Factores de Certeza.

Responsabilidad única: entrada/salida con el usuario. El razonamiento
vive en certainty.py / engine.py; el conocimiento en knowledge.py.
"""

from __future__ import annotations

import argparse
import io
import sys

from engine import CertaintyFactorEngine, TriageResult
from knowledge import DEFAULT_KB, Evidence


# Consolas Windows (cp1252) no imprimen bien algunos caracteres; forzar UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
elif getattr(sys.stdout, "encoding", None) != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


SEP = "=" * 68
THIN = "-" * 68


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sistema Experto de Triage SOC (Factores de Certeza). "
            "Sin argumentos: usa el caso clínico del documento. "
            "Con --interactive: solicita CE por evidencia."
        )
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Solicitar factores de certeza de cada evidencia por consola.",
    )
    parser.add_argument(
        "--e1", type=float, default=None, help="CE(E1) en [-1, 1]",
    )
    parser.add_argument(
        "--e2", type=float, default=None, help="CE(E2) en [-1, 1]",
    )
    parser.add_argument(
        "--e3", type=float, default=None, help="CE(E3) en [-1, 1]",
    )
    parser.add_argument(
        "--e4", type=float, default=None, help="CE(E4) en [-1, 1]",
    )
    return parser.parse_args(argv)


def _prompt_cf(evidence: Evidence) -> float:
    while True:
        raw = input(
            f"  > CE({evidence.code}) [{evidence.default_cf:+.2f}] "
            f"— {evidence.description}\n"
            f"    Factor de certeza [-1, 1] (Enter = default): "
        ).strip()
        if not raw:
            return evidence.default_cf
        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            print("    [ERROR] Ingrese un número válido (ej. 0.85 o -0.40).")
            continue
        if value < -1.0 or value > 1.0:
            print("    [ERROR] El CF debe estar en el intervalo [-1, 1].")
            continue
        return value


def resolve_evidence_cfs(args: argparse.Namespace) -> dict[str, float]:
    defaults = DEFAULT_KB.default_evidence_cfs()
    cli_map = {"E1": args.e1, "E2": args.e2, "E3": args.e3, "E4": args.e4}
    provided = {k: v for k, v in cli_map.items() if v is not None}

    if args.interactive:
        print(f"\n{SEP}")
        print("  INGRESO DE EVIDENCIAS — TRIAGE SOC (Factores de Certeza)")
        print(SEP)
        print("  Un CF negativo indica certeza de que el hecho NO ocurre.\n")
        return {ev.code: _prompt_cf(ev) for ev in DEFAULT_KB.evidences}

    if provided:
        merged = dict(defaults)
        merged.update(provided)
        return merged

    return defaults


def print_report(result: TriageResult) -> None:
    kb = DEFAULT_KB
    print(f"\n{SEP}")
    print("  SISTEMA EXPERTO — TRIAGE DE INCIDENTES DE CIBERSEGURIDAD")
    print("  Motor: Teoría de Factores de Certeza (Caso 2)")
    print(SEP)

    print("\n-- Evidencias (CE) " + "-" * 48)
    for ev in kb.evidences:
        cf = result.evidence_cfs[ev.code]
        note = "  [certeza de NO ocurrencia]" if cf < 0 else ""
        print(f"  {ev.code}: CE = {cf:+.4f}{note}")
        print(f"       {ev.description}")

    print(f"\n-- Evaluación de Reglas " + "-" * 43)
    for re in result.rule_evaluations:
        print(f"  {re.rule.id}: {re.rule.description}")
        print(f"       Antecedente: {re.rule.antecedent.describe()}")
        print(
            f"       CF(antecedente) = {re.cf_antecedent:+.4f}  |  "
            f"CR = {re.rule.cf_rule:+.2f}  |  "
            f"aporte = {re.cf_contribution:+.4f}  [{re.status}]"
        )

    print(f"\n-- Hipótesis (co-suscripción) " + "-" * 36)
    for h in result.hypotheses:
        active = [r.rule.id for r in h.contributing_rules if r.activated]
        sources = ", ".join(active) if active else "(sin aportes activos)"
        print(f"  {h.code} [{h.name}]  CF_final = {h.cf_final:+.4f}")
        print(f"       {h.description}")
        print(f"       Fuentes: {sources}")

    print(f"\n-- Ranking de triage " + "-" * 46)
    for i, h in enumerate(result.ranked, start=1):
        marker = " << PRIORIDAD" if result.primary and h.code == result.primary.code else ""
        print(f"  {i}. {h.code}  {h.name:<16}  CF = {h.cf_final:+.4f}{marker}")

    print(f"\n{THIN}")
    print(f"  DIAGNÓSTICO SOC: {result.explanation}")
    print(f"{SEP}\n")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        evidence_cfs = resolve_evidence_cfs(args)
        engine = CertaintyFactorEngine(DEFAULT_KB)
        result = engine.evaluate(evidence_cfs)
    except (KeyError, ValueError, TypeError) as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        return 1

    print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
