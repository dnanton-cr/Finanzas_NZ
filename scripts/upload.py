#!/usr/bin/env python3
"""
upload.py — Sube transacciones (y opcionalmente presupuesto) a Firestore.

Usa el SDK de Firebase Admin, que requiere una cuenta de servicio:
    Firebase Console → Configuración del proyecto → Cuentas de servicio →
    "Generar nueva clave privada" → descarga el JSON.

Uso:
    pip install -r requirements.txt

    python upload.py data/transacciones.json \
        --service-account /ruta/a/firebase-service-account.json

    # Opcional: subir también el presupuesto mensual
    python upload.py data/transacciones.json \
        --service-account /ruta/a/firebase-service-account.json \
        --presupuesto config/presupuesto.json

El id de documento es un hash determinista de los campos clave, de modo que
volver a subir el mismo estado no duplica transacciones (es idempotente).
"""
import json
import hashlib
import argparse
from pathlib import Path


def doc_id(t: dict, idx: int) -> str:
    clave = "|".join(str(t.get(k, "")) for k in
                     ("tarjeta", "referencia", "fecha", "descripcion", "moneda", "monto"))
    clave += f"|{idx}"  # el índice distingue filas idénticas (p.ej. dos compras iguales el mismo día)
    return hashlib.sha1(clave.encode("utf-8")).hexdigest()[:20]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file", help="JSON de transacciones (salida de parse_bac.py)")
    ap.add_argument("--service-account", required=True,
                    help="ruta al JSON de cuenta de servicio de Firebase")
    ap.add_argument("--collection", default="transacciones")
    ap.add_argument("--presupuesto", default=None,
                    help="JSON de presupuesto (se sube a presupuesto/{mes})")
    args = ap.parse_args()

    from firebase_admin import credentials, firestore, initialize_app
    cred = credentials.Certificate(args.service_account)
    initialize_app(cred)
    db = firestore.client()

    tx = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    batch = db.batch()
    count = 0
    for idx, t in enumerate(tx):
        batch.set(db.collection(args.collection).document(doc_id(t, idx)), t)
        count += 1
        if count % 450 == 0:
            batch.commit()
            batch = db.batch()
    if count % 450 != 0:
        batch.commit()
    print(f"✔ {count} transacciones subidas a la colección '{args.collection}'")

    if args.presupuesto:
        b = json.loads(Path(args.presupuesto).read_text(encoding="utf-8"))
        if "mes" not in b:
            raise SystemExit("El presupuesto debe incluir el campo 'mes' (YYYY-MM).")
        db.collection("presupuesto").document(b["mes"]).set(b)
        print(f"✔ Presupuesto subido para {b['mes']}")


if __name__ == "__main__":
    main()
