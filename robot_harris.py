import os
import requests

def ejecutar_extractor_rentcast():
    print("🚀 Iniciando extracción de datos vía RentCast API...")
    
    # Configuración de endpoints
    API_KEY_RENTCAST = "11474bdd2ab043929287e5ab0e742115"
    URL_RENTCAST = "https://api.rentcast.io/v1/properties"
    
    URL_WEBHOOK_LOVABLE = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    HEADERS_LOVABLE = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }
    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"

    # Parámetros de consulta para Harris County / Houston
    params = {
        "state": "TX",
        "city": "Houston",
        "zipCode": "77002",
        "limit": 5
    }
    
    headers_rentcast = {
        "X-Api-Key": API_KEY_RENTCAST,
        "Accept": "application/json"
    }

    try:
        res = requests.get(URL_RENTCAST, headers=headers_rentcast, params=params, timeout=10)
        
        if res.status_code == 200:
            propiedades = res.json()
            lista_leads = []
            
            for prop in propiedades:
                owner_info = prop.get("owner", {})
                first_name = owner_info.get("firstName", "Owner")
                last_name = owner_info.get("lastName", "Homeowner")
                address = prop.get("addressLine1", "1000 Main St")
                
                lista_leads.append({
                    "user_id": ID_USUARIO_REAL,
                    "first_name": first_name.title() if first_name else "Owner",
                    "last_name": last_name.title() if last_name else "Homeowner",
                    "address": address,
                    "city": prop.get("city", "Houston"),
                    "state": prop.get("state", "TX"),
                    "zip_code": prop.get("zipCode", "77002"),
                    "condado": "Harris"
                })
                print(f"✓ Lead obtenido de API: {first_name} {last_name} - {address}")

            if lista_leads:
                print(f"📡 Transmitiendo {len(lista_leads)} leads a Lovable...")
                resp_webhook = requests.post(URL_WEBHOOK_LOVABLE, json={"leads": lista_leads}, headers=HEADERS_LOVABLE, timeout=15)
                print(f"Respuesta Lovable: {resp_webhook.status_code}")
        else:
            print(f"Error en RentCast API: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"Falla en la consulta: {e}")

if __name__ == "__main__":
    ejecutar_extractor_rentcast()
