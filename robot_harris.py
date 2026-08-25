import os
import time
import requests

def ejecutar_extractor_rentcast():
    print("🚀 Iniciando extracción con mapeo avanzado de propietarios...")
    
    # Coloca tu API Key activa de RentCast
    API_KEY_RENTCAST = "11474bdd2ab043929287e5ab0e742115"
    URL_RENTCAST = "https://api.rentcast.io/v1/properties"
    
    URL_WEBHOOK_LOVABLE = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    HEADERS_LOVABLE = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }
    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"

    # Códigos postales con alta densidad latina y mayor cobertura de nombres
    zips_latinos = ["77039", "77093", "77087", "77083", "77060", "77050"]
    zip_activo = zips_latinos[(int(time.time()) // 60) % len(zips_latinos)]
    print(f"📍 Consultando código postal target: {zip_activo}")

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
                
                # Búsqueda exhaustiva del nombre del propietario en todos los formatos posibles de la API
                raw_names = owner_info.get("names") or owner_info.get("name") or []
                
                if isinstance(raw_names, str):
                    nombre_str = raw_names
                elif isinstance(raw_names, list) and len(raw_names) > 0:
                    nombre_str = str(raw_names[0])
                else:
                    nombre_str = ""

                # Limpieza y formateo
                if nombre_str and nombre_str.strip():
                    # Elimina prefijos comunes de empresas si existen
                    partes = nombre_str.strip().title().split(" ", 1)
                    first_name = partes[0]
                    last_name = partes[1] if len(partes) > 1 else "Propietario"
                else:
                    # En caso de no tener nombre registrado en esa propiedad específica
                    first_name = "Dueño"
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
