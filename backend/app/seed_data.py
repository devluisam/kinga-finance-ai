"""
Dados fictícios para simulação — Kinga Açaí Frozen
Simula 3 lojas + 1 fábrica nos meses de abril e maio/2026.
"""
from datetime import date
import random
from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.models.cost import Cost
from app.models.store import Store
from app.modules.classifier import classify, unit_from_description

random.seed(42)

STORES = [
    ("loja_01", "Loja Centro"),
    ("loja_02", "Loja Shopping"),
    ("loja_03", "Loja Norte"),
]

CHANNELS = ["pdv", "ifood", "delivery"]
CHANNEL_WEIGHTS = [0.60, 0.30, 0.10]

SALES_PER_DAY = {
    "loja_01": (1800, 2800),
    "loja_02": (2500, 4000),
    "loja_03": (1200, 1800),
}

COST_TEMPLATES = [
    # (description, amount_range, unit)
    # FÁBRICA
    ("Compra açaí polpa - fornecedor Norte Frutos", (4000, 5500), "fabrica"),
    ("Compra granola e complementos - fornecedor",  (800, 1200),  "fabrica"),
    ("Compra embalagens copos 300ml/500ml",         (600, 900),   "fabrica"),
    ("Salário fábrica - colaboradores produção",    (4500, 5000), "fabrica"),
    ("Energia elétrica fábrica - CEMIG",            (1200, 1600), "fabrica"),
    ("Frete entrega lojas - transportadora",        (400, 700),   "fabrica"),
    ("Insumos produção fábrica diversos",           (300, 500),   "fabrica"),
    # LOJA 01
    ("Salário loja 1 - atendentes e caixa",         (3500, 4000), "loja_01"),
    ("Aluguel loja 1 - Centro",                     (2800, 2800), "loja_01"),
    ("Energia elétrica loja 1",                     (400, 600),   "loja_01"),
    ("Internet e wi-fi loja 1 - Vivo",              (150, 150),   "loja_01"),
    ("Taxa cartão loja 1 - Stone",                  (300, 500),   "loja_01"),
    ("iFood comissão loja 1",                       (500, 800),   "loja_01"),
    ("Compra material limpeza loja 1",              (100, 200),   "loja_01"),
    ("Água loja 1 - COPASA",                        (80, 120),    "loja_01"),
    ("Marketing Instagram loja 1 - Meta Ads",       (300, 500),   "loja_01"),
    # LOJA 02
    ("Salário loja 2 - atendentes caixa supervisor",(5000, 5500), "loja_02"),
    ("Aluguel loja 2 - Shopping",                   (5500, 5500), "loja_02"),
    ("Energia elétrica loja 2",                     (600, 900),   "loja_02"),
    ("Internet wi-fi loja 2 - Claro",               (150, 150),   "loja_02"),
    ("Taxa cartão loja 2 - Cielo",                  (500, 800),   "loja_02"),
    ("iFood comissão loja 2",                       (700, 1100),  "loja_02"),
    ("Compra material limpeza loja 2",              (120, 200),   "loja_02"),
    ("Água loja 2 - COPASA",                        (100, 150),   "loja_02"),
    ("Manutenção máquina açaí loja 2",              (200, 400),   "loja_02"),
    # LOJA 03
    ("Salário loja 3 - equipe",                     (2800, 3200), "loja_03"),
    ("Aluguel loja 3 - Norte",                      (1800, 1800), "loja_03"),
    ("Energia elétrica loja 3",                     (300, 450),   "loja_03"),
    ("Internet loja 3 - TIM",                       (100, 100),   "loja_03"),
    ("Taxa cartão loja 3",                          (200, 350),   "loja_03"),
    ("iFood comissão loja 3",                       (300, 500),   "loja_03"),
    # ADMIN
    ("Honorários contabilidade escritório",         (800, 800),   "admin"),
    ("DAS Simples Nacional impostos",               (1200, 1800), "admin"),
    ("Pró-labore sócios",                           (3000, 3000), "admin"),
    ("Parcela empréstimo capital de giro banco",    (1500, 1500), "admin"),
    ("Tarifas bancárias conta PJ",                  (80, 120),    "admin"),
]


def seed(db: Session, clear: bool = True) -> None:
    if clear:
        db.query(Sale).delete()
        db.query(Cost).delete()
        db.commit()

    # Semeia lojas se ainda não existirem
    for store_id, store_name in STORES:
        if not db.get(Store, store_id):
            db.add(Store(store_id=store_id, store_name=store_name))
    if not db.get(Store, "fabrica"):
        db.add(Store(store_id="fabrica", store_name="Fábrica"))
    if not db.get(Store, "admin"):
        db.add(Store(store_id="admin", store_name="Administrativo"))
    db.flush()

    for year, month, fat_mult in [(2026, 4, 0.88), (2026, 5, 1.0)]:
        _seed_month(db, year, month, fat_mult)

    db.commit()
    print("[OK] Dados ficticios inseridos com sucesso.")


def _seed_month(db: Session, year: int, month: int, fat_multiplier: float) -> None:
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]

    # Vendas diárias por loja
    for store_id, store_name in STORES:
        low, high = SALES_PER_DAY[store_id]
        for day in range(1, days_in_month + 1):
            day_fat = random.uniform(low * fat_multiplier, high * fat_multiplier)
            for ch, w in zip(CHANNELS, CHANNEL_WEIGHTS):
                ch_amount = round(day_fat * w * random.uniform(0.9, 1.1), 2)
                db.add(Sale(
                    date=date(year, month, day),
                    store_id=store_id,
                    store_name=store_name,
                    channel=ch,
                    amount=ch_amount,
                    source="seed",
                ))

    # Custos mensais
    for description, (low, high), unit in COST_TEMPLATES:
        amount = round(random.uniform(low, high), 2)
        cls = classify(description)
        db.add(Cost(
            date=date(year, month, 5),
            description=description,
            amount=amount,
            category=cls.category,
            subcategory=cls.subcategory,
            unit=unit,
            source="seed",
        ))
