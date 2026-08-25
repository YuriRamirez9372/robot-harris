import os
import time
import requests

def ejecutar_extractor_rentcast():
    print("🚀 Iniciando extracción masiva de 150 leads (Harris County)...")
    
    # Coloca tu API Key activa de RentCast
    API_KEY_RENTCAST = "11474bdd2ab043929287e5ab0e742115"
    URL_RENTCAST = "https://api.rentcast.io/v1/properties"
    
    URL_WEBHOOK_LOVABLE = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    HEADERS_LOVABLE = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }
    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"

    # Códigos postales estratégicos con alta densidad latina
    zips_latinos = ["77039", "77087", "77093", "77017", "77083", "77050"]
    
    # Selecciona un zip code distinto automáticamente por ejecución
    zip_activo = zips_latinos[(int(time.time()) // 60) % len(zips_latinos)]
    print(f"📍 Consultando código postal target: {zip_activo}")

    # Aumentado a 150 registros en una sola consulta API
    params = {
        "state": "TX",
        "zipCode": zip_activo,
        "propertyType": "Single Family",
        "limit": 150
    }
    
    headers_rentcast = {
        "X-Api-Key": API_KEY_RENTCAST,
        "Accept": "application/json"
    }

    try:
        res = requests.get(URL_RENTCAST, headers=headers_rentcast, params=params, timeout=25)
        
        if res.status_code == 200:
            propiedades = res.json()
            lista_leads = []
            
            for prop in propiedades:
                owner_info = prop.get("owner", {})
                
                # Extraer nombres desde la lista 'names' oficial de RentCast
                owner_names = owner_info.get("names", [])
                nombre_completo = owner_names[0] if owner_names and isinstance(owner_names, list) else ""
                
                if nombre_completo:
                    partes = nombre_completo.strip().split(" ", 1)
                    first_name = partes[0].title()
                    last_name = partes[1].title() if len(partes) > 1 else "Propietario"
                else:
                    first_name = "Propietario"
                    last_name = "Residencial"
                
                address = prop.get("addressLine1", "")
                
                if address:
                    lista_leads.append({
                        "user_id": ID_USUARIO_REAL,
                        "first_name": first_name,
                        "last_name": last_name,
                        "address": address,
                        "city": prop.get("city", "Houston"),
                        "state": prop.get("state", "TX"),
                        "zip_code": zip_activo,
                        "condado": "Harris"
                    })
                    print(f"✓ Lead obtenido: {first_name} {last_name} - {address}")

            if lista_leads:
                print(f"📡 Transmitiendo {len(lista_leads)} leads a Lovable...")
                resp_webhook = requests.post(URL_WEBHOOK_LOVABLE, json={"leads": lista_leads}, headers=HEADERS_LOVABLE, timeout=30)
                print(f"Respuesta Lovable: {resp_webhook.status_code}")
        else:
            print(f"Error en RentCast API: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"Falla en la consulta: {e}")

if __name__ == "__main__":
    ejecutar_extractor_rentcast()
