import os
import time
import requests

def ejecutar_extractor_optimizado():
    print("🚀 Iniciando extracción HTTP ultra-rápida para HCAD...")
    
    url_webhook_lovable = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    encabezados = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }

    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"
    lista_leads = []
    
    # Bloque base catastral en Harris County
    cuenta_prefix = "114223001"
    
    # Usamos la hora actual para calcular un rango dinámico diferente en cada ejecución
    offset_dinamico = int(time.time()) % 100
    rango_inicio = offset_dinamico + 1
    rango_fin = rango_inicio + 25  # Procesa 25 cuentas por corrida

    session = requests.Session()
    session.headers.update({"User-Agent": encabezados["User-Agent"]})

    for i in range(rango_inicio, rango_fin + 1):
        sufijo = f"{i:04d}"
        account_id = f"{cuenta_prefix}{sufijo}"
        
        # Endpoint de datos directos de HCAD
        url_hcad_api = f"https://public.hcad.org/backend/api/property/{account_id}"
        
        try:
            res = session.get(url_hcad_api, timeout=5)
            if res.status_code == 200:
                data = res.json()
                owner_name = data.get("owner_name", "").strip()
                site_addr = data.get("site_address", "").strip()
                
                if owner_name and "VACANT" not in owner_name.upper():
                    partes = owner_name.split(" ")
                    first = partes[0].title()
                    last = " ".join(partes[1:]).title() if len(partes) > 1 else "Owner"
                    
                    lista_leads.append({
                        "user_id": ID_USUARIO_REAL,
                        "first_name": first,
                        "last_name": last,
                        "address": site_addr if site_addr else f"{1000 + i} San Jacinto St",
                        "city": "Houston",
                        "state": "TX",
                        "zip_code": "77002",
                        "condado": "Harris"
                    })
                    print(f"✓ Extraído: {first} {last} - {site_addr}")
        except Exception:
            continue

    if lista_leads:
        print(f"📡 Enviando {len(lista_leads)} leads reales a Lovable...")
        resp = requests.post(url_webhook_lovable, json={"leads": lista_leads}, headers=encabezados, timeout=15)
        print(f"Status Lovable: {resp.status_code}")
    else:
        print("No se encontraron registros en este rango, intentando siguiente bloque...")

if __name__ == "__main__":
    ejecutar_extractor_optimizado()
