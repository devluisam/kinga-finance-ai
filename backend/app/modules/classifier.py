"""
Módulo 3 — Classificação Automática de Custos
Usa regras heurísticas por keywords para categorizar despesas.
Quanto mais keywords da regra aparecerem no texto, maior a confiança.
"""
from dataclasses import dataclass
from typing import Optional

RULES: list[tuple[str, str, list[str]]] = [
    # (categoria, subcategoria, keywords)

    # ── FÁBRICA ──────────────────────────────────────────────────────────────
    ("Fábrica", "Matéria-prima", [
        "açaí", "polpa", "acai", "fruta", "granola", "leite condensado",
        "leite ninho", "nutella", "morango", "banana", "manga", "maracuja",
        "maracujá", "abacaxi", "graviola", "cupuacu", "cupuaçu",
        "materia prima", "insumo", "ingrediente", "xarope", "calda",
        "cobertura", "topping", "farinha", "amido", "cacau", "chocolate",
    ]),
    ("Fábrica", "Embalagens", [
        "embalagem", "copo", "tampa", "colher", "saco", "sacola",
        "fita", "etiqueta", "rótulo", "rotulo", "caixinha", "bandeja",
        "plastico", "plástico", "descartavel", "descartável",
    ]),
    ("Fábrica", "Funcionários", [
        "salário fábrica", "salario fabrica", "folha fábrica", "folha fabrica",
        "funcionario fabrica", "funcionário fábrica", "operador", "auxiliar fabrica",
        "producao", "produção", "manipulador",
    ]),
    ("Fábrica", "Energia", [
        "energia fábrica", "luz fabrica", "cemig fabrica", "enel fabrica",
        "energia eletrica fabrica", "conta luz fabrica",
    ]),
    ("Fábrica", "Frete", [
        "frete", "entrega", "transportadora", "logística", "logistica",
        "motoboy fabrica", "frete materia", "frete polpa",
    ]),
    ("Fábrica", "Manutenção", [
        "manutenção fabrica", "manutencao fabrica", "reparo maquina",
        "conserto equipamento", "tecnico fabrica", "freezer", "câmara fria",
        "camara fria", "ultra freezer", "ultrafreeze",
    ]),

    # ── LOJAS ────────────────────────────────────────────────────────────────
    ("Lojas", "Funcionários", [
        "salário loja", "salario loja", "folha loja", "funcionario loja",
        "funcionário loja", "atendente", "caixa loja", "vendedor",
        "promotor", "balconista",
    ]),
    ("Lojas", "Aluguel", [
        "aluguel", "locação", "locacao", "aluguel loja", "condomínio",
        "condominio", "ponto comercial", "iptu", "taxa condominio",
    ]),
    ("Lojas", "Energia", [
        "energia loja", "luz loja", "cemig loja", "enel loja",
        "conta de luz", "energia eletrica loja", "conta energia",
    ]),
    ("Lojas", "Água", [
        "água", "agua", "sabesp", "copasa", "saneago", "caesb",
        "sanepar", "conta agua", "agua e esgoto",
    ]),
    ("Lojas", "Internet / Telefone", [
        "internet", "wi-fi", "wifi", "claro", "vivo", "tim", "oi",
        "net", "banda larga", "telefone", "celular", "chip", "plano",
    ]),
    ("Lojas", "Manutenção", [
        "manutenção", "manutencao", "reparo", "conserto", "técnico",
        "tecnico", "ar condicionado", "ar-condicionado", "geladeira",
        "vitrine refrigerada", "refrigerador",
    ]),
    ("Lojas", "Marketing", [
        "marketing", "publicidade", "propaganda", "panfleto", "impresso",
        "social media", "instagram", "google ads", "meta ads", "facebook ads",
        "tik tok", "tiktok", "influencer", "design", "arte",
    ]),
    ("Lojas", "Taxas Cartão", [
        "taxa cartão", "taxa cartao", "cielo", "stone", "rede", "getnet",
        "pagseguro", "mercado pago", "maquininha", "pos", "pinpad",
        "adquirente", "taxa maquina",
    ]),
    ("Lojas", "iFood / Delivery", [
        "ifood", "rappi", "uber eats", "uber eats", "taxa delivery",
        "comissão delivery", "comissao delivery", "taxa plataforma",
    ]),
    ("Lojas", "Compras Operacionais", [
        "compra loja", "material limpeza", "higiene", "papel toalha",
        "sabão", "sabao", "desinfetante", "vassoura", "pano",
        "utensilio", "utensílios", "copo plastico",
    ]),

    # ── ADMINISTRATIVO ────────────────────────────────────────────────────────
    ("Administrativo", "Contabilidade", [
        "contabilidade", "contador", "escritório contábil",
        "escritorio contabil", "honorario contabil",
    ]),
    ("Administrativo", "Impostos", [
        "imposto", "das", "simples nacional", "icms", "iss", "pis",
        "cofins", "inss", "fgts", "irpj", "csll", "tributo",
        "guia pagamento", "darf", "gps",
    ]),
    ("Administrativo", "Pró-labore", [
        "pró-labore", "pro labore", "prolabore", "retirada sócio",
        "retirada socio", "salario socio",
    ]),
    ("Administrativo", "Empréstimos", [
        "empréstimo", "emprestimo", "parcela empréstimo", "financiamento",
        "parcela banco", "crédito", "credito", "capital giro",
    ]),
    ("Administrativo", "Taxas Bancárias", [
        "taxa bancária", "taxa bancaria", "tarifa bancária", "tarifa bancaria",
        "manutenção conta", "manutencao conta", "ted", "doc", "tarifas banco",
        "tarifa pix", "taxa boleto",
    ]),
    ("Administrativo", "Seguros", [
        "seguro", "apólice", "apolice", "sinistro", "seguro empresarial",
        "seguro incêndio", "seguro incendio",
    ]),
    ("Administrativo", "Sistemas", [
        "sistema", "software", "app", "aplicativo", "erp", "pdv sistema",
        "assinatura", "licença", "licenca", "saas", "plataforma",
    ]),
]


@dataclass
class Classification:
    category: str
    subcategory: str
    confidence: float   # 0.0 a 1.0


def classify(description: str, manual_override: Optional[str] = None) -> Classification:
    """Classifica uma despesa pela descrição."""
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
    best_matches = 0

    for category, subcategory, keywords in RULES:
        # Conta keywords que aparecem + pondera palavras-chave mais longas
        matches = [(kw, len(kw)) for kw in keywords if kw in text]
        if not matches:
            continue
        score = sum(length for _, length in matches)
        n_matches = len(matches)
        if score > best_score or (score == best_score and n_matches > best_matches):
            best_score = score
            best_matches = n_matches
            confidence = min(score / 20, 1.0)
            best = Classification(
                category=category,
                subcategory=subcategory,
                confidence=round(confidence, 2),
            )

    return best or Classification(category="Outros", subcategory="Não classificado", confidence=0.0)


def unit_from_description(description: str) -> str:
    """Tenta inferir a unidade (fábrica / loja / admin) pela descrição."""
    text = description.lower()
    if any(k in text for k in ["fábrica", "fabrica", "produção", "producao", "polpa", "açaí"]):
        return "fabrica"
    for i in range(1, 10):
        if any(k in text for k in [f"loja {i}", f"loja0{i}", f"unidade {i}", f"loja_{i:02d}"]):
            return f"loja_0{i}"
    if any(k in text for k in [
        "admin", "contabilidade", "imposto", "empréstimo", "prolabore",
        "pró-labore", "seguro", "sistema", "software",
    ]):
        return "admin"
    return "loja_01"
