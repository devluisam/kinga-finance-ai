"""
Módulo 3 — Classificação Automática de Custos
Usa regras heurísticas (keywords) para categorizar gastos.
"""
from dataclasses import dataclass
from typing import Optional

RULES: list[tuple[str, str, list[str]]] = [
    # (category, subcategory, keywords)
    # FÁBRICA
    ("Fábrica", "Matéria-prima",  ["açaí", "polpa", "fruta", "granola", "leite condensado", "leite ninho", "nutella", "morango", "banana", "manga", "materia prima", "insumo"]),
    ("Fábrica", "Produção",       ["embalagem", "copo", "tampa", "colher", "saco", "fita", "etiqueta", "rótulo"]),
    ("Fábrica", "Funcionários",   ["salário fábrica", "folha fábrica", "funcionario fabrica", "operador", "auxiliar fabrica"]),
    ("Fábrica", "Energia",        ["energia fábrica", "luz fabrica", "cemig fabrica", "enel fabrica"]),
    ("Fábrica", "Frete",          ["frete", "entrega", "transportadora", "logística", "motoboy fabrica"]),
    # LOJAS
    ("Lojas", "Funcionários",     ["salário loja", "folha loja", "funcionario loja", "atendente", "caixa loja"]),
    ("Lojas", "Aluguel",          ["aluguel", "locação", "aluguel loja", "condomínio"]),
    ("Lojas", "Energia",          ["energia loja", "luz loja", "cemig loja", "enel loja", "conta de luz"]),
    ("Lojas", "Água",             ["água", "sabesp", "copasa", "saneago", "aguá"]),
    ("Lojas", "Internet",         ["internet", "wi-fi", "claro", "vivo", "tim", "oi", "banda larga"]),
    ("Lojas", "Manutenção",       ["manutenção", "reparo", "conserto", "técnico", "manutenção equipamento"]),
    ("Lojas", "Marketing",        ["marketing", "publicidade", "propaganda", "panfleto", "impresso", "social media", "instagram", "google ads", "meta ads"]),
    ("Lojas", "Taxas Cartão",     ["taxa cartão", "cielo", "stone", "rede", "getnet", "pagseguro", "mercado pago", "maquininha"]),
    ("Lojas", "iFood",            ["ifood", "rappi", "uber eats", "taxa delivery", "comissão delivery"]),
    ("Lojas", "Compras Op.",      ["compra loja", "material limpeza", "descartável", "limpeza", "higiene"]),
    # ADMINISTRATIVO
    ("Administrativo", "Contabilidade", ["contabilidade", "contador", "escritório contábil"]),
    ("Administrativo", "Impostos",      ["imposto", "das", "simples nacional", "icms", "iss", "pis", "cofins", "inss", "fgts", "irpj"]),
    ("Administrativo", "Pró-labore",    ["pró-labore", "pro labore", "prolabore", "retirada sócio"]),
    ("Administrativo", "Empréstimos",   ["empréstimo", "parcela empréstimo", "financiamento", "parcela banco"]),
    ("Administrativo", "Taxas Bancárias", ["taxa bancária", "tarifa bancária", "manutenção conta", "ted", "doc", "tarifas"]),
]


@dataclass
class Classification:
    category: str
    subcategory: str
    confidence: float


def classify(description: str, manual_override: Optional[str] = None) -> Classification:
    """Classifica uma despesa pela descrição. Retorna categoria e subcategoria."""
    if manual_override:
        parts = manual_override.split("/", 1)
        return Classification(
            category=parts[0].strip(),
            subcategory=parts[1].strip() if len(parts) > 1 else "",
            confidence=1.0,
        )

    text = description.lower()
    best: Optional[Classification] = None
    best_score = 0

    for category, subcategory, keywords in RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best = Classification(
                category=category,
                subcategory=subcategory,
                confidence=min(score / 2, 1.0),
            )

    return best or Classification(category="Outros", subcategory="Não classificado", confidence=0.0)


def unit_from_description(description: str) -> str:
    """Tenta inferir a unidade (fábrica / loja / admin) pela descrição."""
    text = description.lower()
    if any(k in text for k in ["fábrica", "fabrica", "produção", "producao"]):
        return "fabrica"
    for i in range(1, 10):
        if f"loja {i}" in text or f"loja0{i}" in text or f"unidade {i}" in text:
            return f"loja_0{i}"
    if any(k in text for k in ["admin", "contabilidade", "imposto", "empréstimo", "prolabore", "pró-labore"]):
        return "admin"
    return "loja_01"  # default
