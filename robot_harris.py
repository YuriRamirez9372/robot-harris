import os
import time
import re
import requests

# Expresión regular para filtrar apellidos latinos/hispanos
REGEX_APELLIDOS_LATINOS = re.compile(
    r'\b(Garcia|Rodriguez|Martinez|Hernandez|Lopez|Gonzalez|Perez|Sanchez|Ramirez|Torres|Flores|Rivera|Gomez|Diaz|Cruz|Reyes|Morales|Gutierrez|Ortiz|Ramos|Ruiz|Alvarez|Castillo|Mendoza|Moreno|Jimenez|Romero|Herrera|Medina|Aguilar|Vargas|Guzman|Mendez|Munoz|Salazar|Garza|Soto|Vazquez|Cabrera|Campos|Vega|Fuentes|Carrillo|Valdez|Rios|Solis|Pena|Delgado|Valenzuela|Nunez|Zuniga|Cordero|Trevino|Espinosa|Maldonado|Montero|Tinoco|Borges|Suarez)\b', 
    re.IGNORECASE
)

def es_apellido_latino(nombre_completo):
    return bool(REGEX_APELLIDOS_LATINOS.search(nombre_completo))

def extraer_condados_masivo(modo_semanal=False):
    """
    modo_semanal = False -> Barrido de los últimos 365 días (12 meses)
    modo_semanal = True  -> Actualización de los últimos 7 días
    """
    dias_rango = "*:7" if modo_semanal else "*:365"
    tipo_extraccion = "SEMANAL (últimos 7 días)" if modo_semanal else "BARRIDO COMPLETO (últimos 12 meses)"
    print(f"🚀 Iniciando Extracción Masiva | Modo: {tipo_extraccion}")
    
    API_KEY_RENTCAST = "11474bdd2ab043929287e5ab0e742115"
    URL_RENTCAST = "https://api.rentcast.io/v1/properties"
    
    URL_WEBHOOK_LOVABLE = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    HEADERS_LOVABLE = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }
    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"

    # Lista de condados en los alrededores de Houston
    CONDADOS = ["Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Liberty", "Waller"]
    
    headers_rentcast = {
        "X-Api-Key": API_KEY_RENTCAST,
        "Accept": "application/json"
    }

    total_leads_enviados = 0

    for condado in CONDADOS:
        print(f"\n📍 Extrayendo Condado: {condado} TX...")
        offset = 0
        limit = 500  # Máximo número de registros permitido por la API por petición

        while True:
            params = {
                "state": "TX",
                "county": condado,
                "propertyType": "Single Family",
                "saleDateRange": dias_rango,
                "limit": limit,
                "offset": offset
            }

            try:
                res = requests.get(URL_RENTCAST, headers=headers_rentcast, params=params, timeout=40)
                
                if res.status_code != 200:
                    print(f"⚠️ Error {res.status_code} en {condado} (offset {offset}): {res.text}")
                    break

                propiedades = res.json()
                if not propiedades:
                    print(f"✓ No hay más propiedades en {condado}.")
                    break

                lista_leads = []

                for prop in propiedades:
                    owner_info = prop.get("owner", {})
                    raw_names = owner_info.get("names") or owner_info.get("name") or []
                    
                    if isinstance(raw_names, str):
                        nombre_str = raw_names
                    elif isinstance(raw_names, list) and len(raw_names) > 0:
                        nombre_str = str(raw_names[0])
                    else:
                        nombre_str = ""

                    # Filtrado por coincidencia de apellido latino
                    if nombre_str and nombre_str.strip() and es_apellido_latino(nombre_str):
                        partes = nombre_str.strip().title().split(" ", 1)
                        first_name = partes[0]
                        last_name = partes[1] if len(partes) > 1 else "Propietario"
                        
                        address = prop.get("addressLine1", "")
                        last_sale = prop.get("lastSale", {})
                        fecha_compra = last_sale.get("date", "") if last_sale else ""
                        
                        if address:
                            lista_leads.append({
                                "user_id": ID_USUARIO_REAL,
                                "first_name": first_name,
                                "last_name": last_name,
                                "address": address,
                                "city": prop.get("city", "Houston"),
                                "state": prop.get("state", "TX"),
                                "zip_code": prop.get("zipCode", ""),
                                "condado": condado,
                                "purchase_date": fecha_compra
                            })

                # Transmitir bloque recolectado a Lovable
                if lista_leads:
                    print(f"📡 Enviando {len(lista_leads)} leads latinos a Lovable (Condado: {condado}, Offset: {offset})...")
                    resp_webhook = requests.post(URL_WEBHOOK_LOVABLE, json={"leads": lista_leads}, headers=HEADERS_LOVABLE, timeout=30)
                    total_leads_enviados += len(lista_leads)

                # Control de fin de paginación
                if len(propiedades) < limit:
                    print(f"✓ Fin de registros para {condado}.")
                    break
                
                # Avanzar offset para la siguiente llamada
                offset += limit
                time.sleep(1) # Pausa preventiva para respetar rate limits

            except Exception as e:
                print(f"❌ Error durante la ejecución en {condado}: {e}")
                break

    print(f"\n🎉 Extracción finalizada. Total de leads latinos procesados: {total_leads_enviados}")

if __name__ == "__main__":
    # Para el primer barrido masivo (12 meses):
    extraer_condados_masivo(modo_semanal=False)

    # Para la automatización semanal programada en el cron job, cambiarías a:
    # extraer_condados_masivo(modo_semanal=True)
