"""
Módulos 4 e 5 — Resultado Operacional e Indicadores
Pergunta: Houve lucro ou prejuízo?
"""
from dataclasses import dataclass


@dataclass
class OperationalResult:
    faturamento: float
    custos: float
    resultado: float
    margem_pct: float
    custo_pct: float
    status: str        # "LUCRO" | "PREJUÍZO" | "EQUILÍBRIO"
    variacao_faturamento: float
    variacao_custos: float


def compute_result(
    faturamento: float,
    custos: float,
    variacao_faturamento: float = 0.0,
    variacao_custos: float = 0.0,
) -> OperationalResult:
    resultado = round(faturamento - custos, 2)
    margem = round(resultado / faturamento * 100, 2) if faturamento > 0 else 0.0
    custo_pct = round(custos / faturamento * 100, 2) if faturamento > 0 else 0.0

    if resultado > 0:
        status = "LUCRO"
    elif resultado < 0:
        status = "PREJUÍZO"
    else:
        status = "EQUILÍBRIO"

    return OperationalResult(
        faturamento=faturamento,
        custos=custos,
        resultado=resultado,
        margem_pct=margem,
        custo_pct=custo_pct,
        status=status,
        variacao_faturamento=variacao_faturamento,
        variacao_custos=variacao_custos,
    )


@dataclass
class StoreResult:
    store_id: str
    store_name: str
    faturamento: float
    custos: float
    resultado: float
    margem_pct: float


def compute_store_results(
    revenue_by_store: dict[str, float],
    costs_by_unit: dict[str, float],
    store_map: dict[str, str],  # unit_id → store_name
) -> list[StoreResult]:
    results = []
    for store_name, fat in revenue_by_store.items():
        unit_id = next((k for k, v in store_map.items() if v == store_name), store_name.lower().replace(" ", "_"))
        custo = costs_by_unit.get(unit_id, 0.0)
        resultado = round(fat - custo, 2)
        margem = round(resultado / fat * 100, 2) if fat > 0 else 0.0
        results.append(
            StoreResult(
                store_id=unit_id,
                store_name=store_name,
                faturamento=fat,
                custos=custo,
                resultado=resultado,
                margem_pct=margem,
            )
        )
    return sorted(results, key=lambda x: x.faturamento, reverse=True)
