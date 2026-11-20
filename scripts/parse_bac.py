#!/usr/bin/env python3
"""
parse_bac.py — Parsea un estado de cuenta de tarjeta de crédito BAC Credomatic
y extrae las transacciones de la sección "B) Detalle de compras del periodo".

Uso:
    python parse_bac.py <pdf> [-o salida.json] [-c categorias.json]

Cada transacción se normaliza a un registro JSON con:
    fecha, mes, persona, tarjeta, referencia, descripcion, lugar,
    moneda, monto, monto_usd, categoria

La persona se asigna según los últimos 4 dígitos de la sub-tarjeta.
`monto_usd` es el monto normalizado a dólares: CRC→USD (tasa_usd_crc),
USD se mantiene y EUR→USD (tasa_eur_usd). Tasas en config/categorias.json.
"""
import re
import json
import sys
import argparse
from pathlib import Path

MESES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}

PAISES = {
    "DEU": "Alemania", "CRI": "Costa Rica", "USA": "Estados Unidos",
    "SGP": "Singapur", "LUX": "Luxemburgo", "LTU": "Lituania",
    "HKG": "Hong Kong", "NLD": "Países Bajos", "GBR": "Reino Unido",
}

# Líneas de encabezado / ruido del PDF que hay que ignorar
NOISE = {
    "TARJETA DE CREDITO", "N. Referencia", "Fecha de pago",
    "Concepto/Descripción", "Lugar", "Moneda", "Monto en colones",
    "Monto en dólares", "Movimientos de la tarjeta de crédito",
}

CARD_RE = re.compile(r"^\*{6,}(\d{4})$")
REF_RE = re.compile(r"^\d{9,14}$")
DATE_RE = re.compile(r"^(\d{1,2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(\d{2})$", re.I)


def parse_monto(s: str):
    s = s.strip().replace(",", "")
    negativo = s.endswith("-")
    if negativo:
        s = s[:-1]
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if negativo else v


def parse_fecha(s: str):
    m = DATE_RE.match(s.strip())
    if not m:
        return None
    dia = int(m.group(1))
    mes = MESES[m.group(2).upper()]
    anio = 2000 + int(m.group(3))
    return f"{anio:04d}-{mes:02d}-{dia:02d}"


def fecha_desde_referencia(ref: str, anio: int = None):
    """Si el PDF no trae fecha, se infiere del número de referencia BAC (MMDD al inicio).
    Es la fecha de registro BAC; puede diferir 1-2 días de la fecha de compra."""
    m = re.match(r"^(\d{2})(\d{2})\d+$", (ref or "").strip())
    if not m:
        return None
    mm, dd = int(m.group(1)), int(m.group(2))
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return None
    from datetime import date
    anio = anio or date.today().year
    return f"{anio:04d}-{mm:02d}-{dd:02d}"


def extraer_lugar(desc: str):
    """Intenta extraer el código de país (DEU, CRI, ...) al final de la descripción."""
    codes = re.findall(r"\b([A-Z]{3})\b", desc)
    for c in reversed(codes):
        if c in PAISES:
            return c
    return None


def categorizar(desc: str, config: dict):
    d = desc.lower()
    for cat in config.get("categorias", []):
        for kw in cat.get("keywords", []):
            if kw.lower() in d:
                return cat["nombre"]
    return config.get("otros_nombre", "Otros")


def a_usd(moneda: str, monto: float, config: dict):
    """Normaliza el monto a dólares: CRC→USD, USD se mantiene, EUR→USD."""
    if moneda == "CRC":
        return round(monto / config.get("tasa_usd_crc", 445.0), 2)
    if moneda == "EUR":
        return round(monto * config.get("tasa_eur_usd", 1.08), 2)
    return monto


def extraer_texto(pdf_path: str):
    import pymupdf
    doc = pymupdf.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)


def parsear(texto: str, config: dict):
    lines = texto.split("\n")

    # Localizar la sección B) Detalle de compras
    start = None
    end = None
    for i, l in enumerate(lines):
        if "Detalle de compras del periodo" in l and start is None:
            start = i
        if "Total de compras del periodo" in l and start is not None:
            end = i
            break
    if start is None or end is None:
        raise ValueError("No se encontró la sección 'Detalle de compras del periodo'.")

    section = lines[start:end]

    # Identificar sub-tarjetas (encabezado + nombre)
    segmentos = []  # (ultimos4, nombre, idx_nombre)
    for i, line in enumerate(section):
        m = CARD_RE.match(line.strip())
        if m:
            j = i + 1
            while j < len(section):
                s = section[j].strip()
                if s and s not in NOISE:
                    break
                j += 1
            nombre = section[j].strip() if j < len(section) else ""
            segmentos.append((m.group(1), nombre, j))

    personas = config.get("personas", {})

    def nombre_persona(card: str, nombre_crudo: str):
        if card in personas:
            return personas[card]
        # fallback: primer token del nombre
        return nombre_crudo.split("/")[0].strip().title() if nombre_crudo else card

    transacciones = []
    for idx, (card, nombre_crudo, nombre_idx) in enumerate(segmentos):
        fin = segmentos[idx + 1][2] if idx + 1 < len(segmentos) else len(section)
        bloque = section[nombre_idx + 1:fin]

        limpio = [
            l.strip() for l in bloque
            if l.strip()
            and l.strip() not in NOISE
            and not l.strip().startswith("B) Detalle")
            and not l.strip().startswith("Movimientos")
            and not l.strip().startswith("Página")
        ]

        persona = nombre_persona(card, nombre_crudo)

        i = 0
        n = len(limpio)
        while i < n:
            if not REF_RE.match(limpio[i]):
                i += 1
                continue
            ref = limpio[i]
            i += 1
            if i >= n:
                break
            fecha = parse_fecha(limpio[i]) or fecha_desde_referencia(ref)
            i += 1
            desc_parts = []
            while i < n and limpio[i] not in ("USD", "CRC", "EUR") and not REF_RE.match(limpio[i]):
                desc_parts.append(limpio[i])
                i += 1
            if i >= n:
                break
            moneda = limpio[i]
            i += 1
            if i >= n:
                break
            monto = parse_monto(limpio[i])
            i += 1

            desc = " ".join(desc_parts).strip()
            lugar = extraer_lugar(desc)
            cat = categorizar(desc, config)

            transacciones.append({
                "fecha": fecha,
                "mes": fecha[:7] if fecha else None,
                "persona": persona,
                "tarjeta": card,
                "referencia": ref,
                "descripcion": desc,
                "lugar": PAISES.get(lugar, lugar) if lugar else None,
                "moneda": moneda,
                "monto": monto,
                "monto_usd": a_usd(moneda, monto, config),
                "categoria": cat,
            })

    return transacciones


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("-c", "--config", default=str(Path(__file__).resolve().parent.parent / "config" / "categorias.json"))
    args = ap.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    texto = extraer_texto(args.pdf)
    tx = parsear(texto, config)

    # Resumen
    personas = {}
    categorias = {}
    total_crc = 0.0
    total_usd_nativo = 0.0
    total_eur_nativo = 0.0
    total_usd = 0.0
    for t in tx:
        personas[t["persona"]] = personas.get(t["persona"], 0) + 1
        categorias[t["categoria"]] = categorias.get(t["categoria"], 0) + 1
        m = t["monto"] or 0
        if t["moneda"] == "CRC":
            total_crc += m
        elif t["moneda"] == "EUR":
            total_eur_nativo += m
        else:
            total_usd_nativo += m
        total_usd += t["monto_usd"] or 0

    print(f"Transacciones: {len(tx)}")
    print(f"Por persona: {json.dumps(personas, ensure_ascii=False)}")
    print(f"Por categoría: {json.dumps(categorias, ensure_ascii=False)}")
    print(f"Total CRC (nativo): {total_crc:,.2f}")
    print(f"Total USD (nativo): {total_usd_nativo:,.2f}")
    if total_eur_nativo:
        print(f"Total EUR (nativo): {total_eur_nativo:,.2f}")
    print(f"Total en USD (normalizado): {total_usd:,.2f}")

    out = args.output or str(Path(args.pdf).with_suffix(".json"))
    Path(out).write_text(json.dumps(tx, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito: {out}")


if __name__ == "__main__":
    main()
