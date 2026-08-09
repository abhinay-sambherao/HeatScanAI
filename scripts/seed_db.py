"""Seed the database with realistic EPREL data for development.

Usage:
    cd HeatScanAI/backend
    python -m scripts.seed_db

Run from the backend/ directory.
"""

import asyncio
import uuid
from datetime import date

from app.database import async_session_factory, engine, Base
from app.models.manufacturer import Manufacturer
from app.models.category import Category
from app.models.product import Product


MANUFACTURERS = [
    # German
    "Viessmann",
    "Vaillant",
    "Buderus",
    "Bosch",
    "Wolf",
    "Stiebel Eltron",
    "Protherm",
    "Vailant",
    "Baxi",
    # Italian
    "Ariston",
    "Ferroli",
    "Beretta",
    "Rinnai",
    # Japanese
    "Daikin",
    "Mitsubishi Electric",
    "Panasonic",
    "Hitachi",
    # Swedish / Nordic
    "NIBE",
    "Mitsubishi Heavy Industries",
    # UK
    "Worcester Bosch",
    "Glow-worm",
    # Others
    "Remeha",
    "Intergas",
    "ATAG",
    "AWB",
    "Beka",
    "Biasi",
]

CATEGORIES = [
    {"name": "Gas boilers", "eprel_id": "491"},
    {"name": "Oil boilers", "eprel_id": "492"},
    {"name": "Heat pumps - Air-to-water", "eprel_id": "494-1"},
    {"name": "Heat pumps - Ground-source", "eprel_id": "494-2"},
    {"name": "Heat pumps - Exhaust air", "eprel_id": "494-3"},
    {"name": "Combination heaters", "eprel_id": "495"},
    {"name": "Solar thermal collectors", "eprel_id": "496"},
    {"name": "Biomass boilers", "eprel_id": "497"},
    {"name": "Warm air heaters", "eprel_id": "498"},
]

# fmt: off
PRODUCTS = [
    # ─── Gas boilers ───────────────────────────────────────────────
    {"eprel_id": "EPREL-001", "model": "Vitodens 200-W B2HA", "energy_class": "A", "fuel_type": "gas", "heat_output": "24 kW", "manufacturer": "Viessmann", "category": "Gas boilers", "efficiency": "92%"},
    {"eprel_id": "EPREL-002", "model": "Vitodens 100-W B1KA", "energy_class": "A", "fuel_type": "gas", "heat_output": "20 kW", "manufacturer": "Viessmann", "category": "Gas boilers", "efficiency": "90%"},
    {"eprel_id": "EPREL-003", "model": "Vitodens 300-W B3HE", "energy_class": "A", "fuel_type": "gas", "heat_output": "35 kW", "manufacturer": "Viessmann", "category": "Gas boilers", "efficiency": "93%"},
    {"eprel_id": "EPREL-004", "model": "Logamax Plus GB142-28", "energy_class": "B", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Buderus", "category": "Gas boilers", "efficiency": "88%"},
    {"eprel_id": "EPREL-005", "model": "Logamax Plus GB172i-35", "energy_class": "A", "fuel_type": "gas", "heat_output": "35 kW", "manufacturer": "Buderus", "category": "Gas boilers", "efficiency": "92%"},
    {"eprel_id": "EPREL-006", "model": "ecoTEC plus 837 VUW", "energy_class": "A", "fuel_type": "gas", "heat_output": "30 kW", "manufacturer": "Vaillant", "category": "Gas boilers", "efficiency": "91%"},
    {"eprel_id": "EPREL-007", "model": "ecoTEC plus 832 VUW", "energy_class": "A", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Vaillant", "category": "Gas boilers", "efficiency": "90%"},
    {"eprel_id": "EPREL-008", "model": "ecoTEC pro 282 VUW", "energy_class": "B", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Vaillant", "category": "Gas boilers", "efficiency": "87%"},
    {"eprel_id": "EPREL-009", "model": "Condens 7000i WBC33", "energy_class": "A", "fuel_type": "gas", "heat_output": "33 kW", "manufacturer": "Bosch", "category": "Gas boilers", "efficiency": "94%"},
    {"eprel_id": "EPREL-010", "model": "Condens 5000i WBC28", "energy_class": "A", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Bosch", "category": "Gas boilers", "efficiency": "92%"},
    {"eprel_id": "EPREL-011", "model": "Cerasmart 230", "energy_class": "A", "fuel_type": "gas", "heat_output": "20 kW", "manufacturer": "Bosch", "category": "Gas boilers", "efficiency": "89%"},
    {"eprel_id": "EPREL-012", "model": "CGi-28", "energy_class": "A", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Wolf", "category": "Gas boilers", "efficiency": "91%"},
    {"eprel_id": "EPREL-013", "model": "MCR-3 28T", "energy_class": "B", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Protherm", "category": "Gas boilers", "efficiency": "86%"},
    {"eprel_id": "EPREL-014", "model": "MCR-3 35T", "energy_class": "A", "fuel_type": "gas", "heat_output": "35 kW", "manufacturer": "Protherm", "category": "Gas boilers", "efficiency": "90%"},
    {"eprel_id": "EPREL-015", "model": "GreenStar 8000 Life 30", "energy_class": "A", "fuel_type": "gas", "heat_output": "30 kW", "manufacturer": "Worcester Bosch", "category": "Gas boilers", "efficiency": "94%"},
    {"eprel_id": "EPREL-016", "model": "GreenStar CDi Classic 34", "energy_class": "A", "fuel_type": "gas", "heat_output": "34 kW", "manufacturer": "Worcester Bosch", "category": "Gas boilers", "efficiency": "93%"},
    {"eprel_id": "EPREL-017", "model": "Eclipse A 28", "energy_class": "A", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Glow-worm", "category": "Gas boilers", "efficiency": "89%"},
    {"eprel_id": "EPREL-018", "model": "EASYGEN 323S", "energy_class": "A", "fuel_type": "gas", "heat_output": "32 kW", "manufacturer": "Remeha", "category": "Gas boilers", "efficiency": "92%"},
    {"eprel_id": "EPREL-019", "model": "Excellent 28C", "energy_class": "A", "fuel_type": "gas", "heat_output": "28 kW", "manufacturer": "Intergas", "category": "Gas boilers", "efficiency": "94%"},
    {"eprel_id": "EPREL-020", "model": "Combi 32S", "energy_class": "B", "fuel_type": "gas", "heat_output": "32 kW", "manufacturer": "ATAG", "category": "Gas boilers", "efficiency": "88%"},

    # ─── Oil boilers ───────────────────────────────────────────────
    {"eprel_id": "EPREL-021", "model": "Vitola 200-B 35", "energy_class": "B", "fuel_type": "oil", "heat_output": "35 kW", "manufacturer": "Viessmann", "category": "Oil boilers", "efficiency": "87%"},
    {"eprel_id": "EPREL-022", "model": "Paromat top 100", "energy_class": "B", "fuel_type": "oil", "heat_output": "40 kW", "manufacturer": "Buderus", "category": "Oil boilers", "efficiency": "85%"},
    {"eprel_id": "EPREL-023", "model": "Logano GE515", "energy_class": "C", "fuel_type": "oil", "heat_output": "50 kW", "manufacturer": "Buderus", "category": "Oil boilers", "efficiency": "82%"},
    {"eprel_id": "EPREL-024", "model": "GreenstarOil 2000 30", "energy_class": "B", "fuel_type": "oil", "heat_output": "30 kW", "manufacturer": "Worcester Bosch", "category": "Oil boilers", "efficiency": "86%"},
    {"eprel_id": "EPREL-025", "model": "TurboMAX Plus 35S", "energy_class": "C", "fuel_type": "oil", "heat_output": "35 kW", "manufacturer": "Ferroli", "category": "Oil boilers", "efficiency": "81%"},

    # ─── Heat pumps - Air-to-water ─────────────────────────────────
    {"eprel_id": "EPREL-026", "model": "Vitocal 250-A 251.A08", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "8.2 kW", "manufacturer": "Viessmann", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.8"},
    {"eprel_id": "EPREL-027", "model": "Vitocal 250-A 251.A13", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "13 kW", "manufacturer": "Viessmann", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.6"},
    {"eprel_id": "EPREL-028", "model": "Vitocal 250-A 251.A19", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "19 kW", "manufacturer": "Viessmann", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.5"},
    {"eprel_id": "EPREL-029", "model": "aroTHERM plus VWL 75/6", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "7.8 kW", "manufacturer": "Vaillant", "category": "Heat pumps - Air-to-water", "efficiency": "COP 5.1"},
    {"eprel_id": "EPREL-030", "model": "aroTHERM plus VWL 105/6", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "10.7 kW", "manufacturer": "Vaillant", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.9"},
    {"eprel_id": "EPREL-031", "model": "aroTHERM plus VWL 145/6", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "14.5 kW", "manufacturer": "Vaillant", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.7"},
    {"eprel_id": "EPREL-032", "model": "Altherma 3H ERHVA16", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "16 kW", "manufacturer": "Daikin", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.6"},
    {"eprel_id": "EPREL-033", "model": "Altherma 3H ERHVA11", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "11 kW", "manufacturer": "Daikin", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.8"},
    {"eprel_id": "EPREL-034", "model": "Ecodan PUHZ-HW140", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "14 kW", "manufacturer": "Mitsubishi Electric", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.2"},
    {"eprel_id": "EPREL-035", "model": "Ecodan PUHZ-HW50", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "5 kW", "manufacturer": "Mitsubishi Electric", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.4"},
    {"eprel_id": "EPREL-036", "model": "Aquarea J Series J30", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "9 kW", "manufacturer": "Panasonic", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.7"},
    {"eprel_id": "EPREL-037", "model": "Aquarea L Series L16", "energy_class": "A+", "fuel_type": "electricity", "heat_output": "16 kW", "manufacturer": "Panasonic", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.1"},
    {"eprel_id": "EPREL-038", "model": "WPL 18 Classic", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "18 kW", "manufacturer": "Wolf", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.5"},
    {"eprel_id": "EPREL-039", "model": "CS5828i AW-HP-E-250", "energy_class": "A+", "fuel_type": "electricity", "heat_output": "25 kW", "manufacturer": "Mitsubishi Heavy Industries", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.0"},
    {"eprel_id": "EPREL-040", "model": "HPA-O 4 Compact", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "4.7 kW", "manufacturer": "Stiebel Eltron", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.9"},
    {"eprel_id": "EPREL-041", "model": "HPA-O 8 Compact", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "8.2 kW", "manufacturer": "Stiebel Eltron", "category": "Heat pumps - Air-to-water", "efficiency": "COP 4.8"},

    # ─── Heat pumps - Ground-source ────────────────────────────────
    {"eprel_id": "EPREL-042", "model": "Vitocal 350-G 350.GA11", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "11 kW", "manufacturer": "Viessmann", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.2"},
    {"eprel_id": "EPREL-043", "model": "Vitocal 350-G 350.GA17", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "17 kW", "manufacturer": "Viessmann", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.0"},
    {"eprel_id": "EPREL-044", "model": "geoTHERM plus VWL 85/2", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "8.5 kW", "manufacturer": "Vaillant", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.3"},
    {"eprel_id": "EPREL-045", "model": "geoTHERM plus VWL 135/2", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "13.5 kW", "manufacturer": "Vaillant", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.1"},
    {"eprel_id": "EPREL-046", "model": "NIBE F1345-12", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "12 kW", "manufacturer": "NIBE", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.0"},
    {"eprel_id": "EPREL-047", "model": "NIBE F1345-18", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "18 kW", "manufacturer": "NIBE", "category": "Heat pumps - Ground-source", "efficiency": "COP 4.8"},
    {"eprel_id": "EPREL-048", "model": "WPL 25 Classic", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "25 kW", "manufacturer": "Wolf", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.1"},
    {"eprel_id": "EPREL-050", "model": "EWPE-C 060C", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "6 kW", "manufacturer": "Stiebel Eltron", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.4"},
    {"eprel_id": "EPREL-051", "model": "EWPE-C 012C", "energy_class": "A++", "fuel_type": "electricity", "heat_output": "12 kW", "manufacturer": "Stiebel Eltron", "category": "Heat pumps - Ground-source", "efficiency": "COP 5.2"},

    # ─── Combination heaters (gas + solar) ─────────────────────────
    {"eprel_id": "EPREL-052", "model": "Vitodens 200-W + Solar", "energy_class": "A", "fuel_type": "gas", "heat_output": "24 kW", "manufacturer": "Viessmann", "category": "Combination heaters", "efficiency": "93%"},
    {"eprel_id": "EPREL-053", "model": "ecoTEC plus + aroCOLLECT", "energy_class": "A", "fuel_type": "gas", "heat_output": "30 kW", "manufacturer": "Vaillant", "category": "Combination heaters", "efficiency": "92%"},
    {"eprel_id": "EPREL-054", "model": "GreenStar 8000 Life + Solar", "energy_class": "A", "fuel_type": "gas", "heat_output": "30 kW", "manufacturer": "Worcester Bosch", "category": "Combination heaters", "efficiency": "94%"},

    # ─── Biomass boilers ───────────────────────────────────────────
    {"eprel_id": "EPREL-055", "model": "Vitoligno 300-C 40", "energy_class": "A", "fuel_type": "biomass", "heat_output": "40 kW", "manufacturer": "Viessmann", "category": "Biomass boilers", "efficiency": "92%"},
    {"eprel_id": "EPREL-056", "model": "Vitoligno 300-C 80", "energy_class": "A", "fuel_type": "biomass", "heat_output": "80 kW", "manufacturer": "Viessmann", "category": "Biomass boilers", "efficiency": "91%"},
    {"eprel_id": "EPREL-057", "model": "Logano GE615 50", "energy_class": "B", "fuel_type": "biomass", "heat_output": "50 kW", "manufacturer": "Buderus", "category": "Biomass boilers", "efficiency": "88%"},
    {"eprel_id": "EPREL-058", "model": "SBG 30-100", "energy_class": "A", "fuel_type": "biomass", "heat_output": "100 kW", "manufacturer": "Wolf", "category": "Biomass boilers", "efficiency": "90%"},

    # ─── Solar thermal ─────────────────────────────────────────────
    {"eprel_id": "EPREL-059", "model": "Vitosol 200-FM", "energy_class": "A", "fuel_type": "solar", "heat_output": "2.52 m²", "manufacturer": "Viessmann", "category": "Solar thermal collectors", "efficiency": "78%"},
    {"eprel_id": "EPREL-060", "model": "Vitosol 300-FM", "energy_class": "A", "fuel_type": "solar", "heat_output": "3.02 m²", "manufacturer": "Viessmann", "category": "Solar thermal collectors", "efficiency": "82%"},
    {"eprel_id": "EPREL-061", "model": "FKK-AE 2.0", "energy_class": "A", "fuel_type": "solar", "heat_output": "2.0 m²", "manufacturer": "Wolf", "category": "Solar thermal collectors", "efficiency": "76%"},

    # ─── Warm air heaters ──────────────────────────────────────────
    # NOTE: no seed entries — "Weishaupt WarmAir 3000" was verified as
    # non-existent and removed (never seeded into the live database).

    # ─── Additional real-world popular models ───────────────────────
    {"eprel_id": "EPREL-064", "model": "Ariston Clas One 25", "energy_class": "A", "fuel_type": "gas", "heat_output": "25 kW", "manufacturer": "Ariston", "category": "Gas boilers", "efficiency": "89%"},
    {"eprel_id": "EPREL-065", "model": "Ariston Clas One 30", "energy_class": "A", "fuel_type": "gas", "heat_output": "30 kW", "manufacturer": "Ariston", "category": "Gas boilers", "efficiency": "90%"},
    {"eprel_id": "EPREL-066", "model": "Ariston Genus One 35", "energy_class": "A", "fuel_type": "gas", "heat_output": "35 kW", "manufacturer": "Ariston", "category": "Gas boilers", "efficiency": "91%"},
    {"eprel_id": "EPREL-067", "model": "Ferroli Blue Helix 32", "energy_class": "A", "fuel_type": "gas", "heat_output": "32 kW", "manufacturer": "Ferroli", "category": "Gas boilers", "efficiency": "88%"},
    {"eprel_id": "EPREL-068", "model": "Beretta Ciao 32 CS", "energy_class": "B", "fuel_type": "gas", "heat_output": "32 kW", "manufacturer": "Beretta", "category": "Gas boilers", "efficiency": "86%"},
    {"eprel_id": "EPREL-069", "model": "Rinnai i240S", "energy_class": "A", "fuel_type": "gas", "heat_output": "24 kW", "manufacturer": "Rinnai", "category": "Gas boilers", "efficiency": "87%"},
    {"eprel_id": "EPREL-070", "model": "Baxi Duo-tec MP+ 40", "energy_class": "A", "fuel_type": "gas", "heat_output": "40 kW", "manufacturer": "Baxi", "category": "Gas boilers", "efficiency": "90%"},

    # ─── Heat pump - exhaust air ───────────────────────────────────
    {"eprel_id": "EPREL-071", "model": "EAH-A 5500", "energy_class": "A+", "fuel_type": "electricity", "heat_output": "5.5 kW", "manufacturer": "Stiebel Eltron", "category": "Heat pumps - Exhaust air", "efficiency": "COP 3.8"},
    {"eprel_id": "EPREL-072", "model": "CombiAir 260", "energy_class": "A+", "fuel_type": "electricity", "heat_output": "4.8 kW", "manufacturer": "NIBE", "category": "Heat pumps - Exhaust air", "efficiency": "COP 3.6"},
]
# fmt: on


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        mfrs = {}
        for name in MANUFACTURERS:
            mfr = Manufacturer(id=uuid.uuid4(), name=name)
            db.add(mfr)
            mfrs[name] = mfr

        cats = {}
        for cat_data in CATEGORIES:
            cat = Category(id=uuid.uuid4(), name=cat_data["name"], eprel_category_id=cat_data["eprel_id"])
            db.add(cat)
            cats[cat_data["name"]] = cat

        for p in PRODUCTS:
            product = Product(
                id=uuid.uuid4(),
                eprel_id=p["eprel_id"],
                manufacturer_id=mfrs[p["manufacturer"]].id,
                category_id=cats[p["category"]].id,
                model=p["model"],
                energy_class=p["energy_class"],
                fuel_type=p["fuel_type"],
                heat_output=p["heat_output"],
                efficiency=p.get("efficiency"),
            )
            db.add(product)

        await db.commit()
        print(f"Seeded {len(MANUFACTURERS)} manufacturers, {len(CATEGORIES)} categories, {len(PRODUCTS)} products")


if __name__ == "__main__":
    asyncio.run(seed())
