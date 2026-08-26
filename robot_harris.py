import os
import csv
import re
import requests

# Expresión regular para filtrar apellidos latinos/hispanos
REGEX_APELLIDOS_LATINOS = re.compile(
    r'\b(Garcia|Rodriguez|Martinez|Hernandez|Lopez|Gonzalez|Perez|Sanchez|Ramirez|Torres|Flores|Rivera|Gomez|Diaz|Cruz|Reyes|Morales|Gutierrez|Ortiz|Ramos|Ruiz|Alvarez|Castillo|Mendoza|Moreno|Jimenez|Romero|Herrera|Medina|Aguilar|Vargas|Guzman|Mendez|Munoz|Salazar|Garza|Soto|Vazquez|Cabrera|Campos|Vega|Fuentes|Carrillo|Valdez|Rios|Solis|Pena|Delgado|Valenzuela|Nunez|Zuniga|Cordero|Trevino|Espinosa|Maldonado|Montero|Tinoco|Borges|Suarez)\b', 
    re.IGNORECASE
)

def es_apellido_latino(nombre_completo):
    """Verifica si el nombre contiene patrones latinos"""
    return bool(REGEX_APELLIDOS_LATINOS.search(nombre_completo))

def guardar_csv_por_zip(condado, zip_code, leads):
    """Crea la estructura de carpetas: archivos_leads/Condado/ZipCode/ y guarda el CSV"""
    directorio = os.path.join("archivos_leads", condado, str(zip_code))
    os.makedirs(directorio, exist_ok=True)
    
    filepath = os.path.join(directorio, f"leads_{condado}_{zip_code}.csv")
    
    # Encabezados limpios listos para importar
    headers = ["first_name", "last_name", "address", "city", "state", "zip_code", "condado", "purchase_date"]
    
    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(leads)
        
    print(f"  📁 File generado: {filepath} ({len(leads)} leads)")

def ejecutar_barrido_rentcast(modo_semanal=False):
    """
    modo_semanal = False -> Barrido histórico inicial (últimos 365 días)
    modo_semanal = True  -> Actualización semanal continua (últimos 7 días)
    """
    dias_rango = "*:7" if modo_semanal else "*:365"
    tipo = "SEMANAL (7 días)" if modo_semanal else "HISTÓRICO (12 meses)"
    print(f"🚀 Iniciando Generación de CSVs | Modo: {tipo}\n")
    
    API_KEY_RENTCAST = "11474bdd2ab043929287e5ab0e742115"  # Reemplazar por tu clave de RentCast
    URL_RENTCAST = "https://api.rentcast.io/v1/properties"
    
    # 7 Condados del Área Metropolitana de Houston
    CONDADOS = ["Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Liberty", "Waller"]
    headers_rentcast = {"X-Api-Key": API_KEY_RENTCAST, "Accept": "application/json"}

    for condado in CONDADOS:
        print(f"📍 Procesando Condado: {condado} TX...")
        offset = 0
        limit = 500  # Paginación al máximo de la API
        leads_por_zip = {}

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
                    break

                for prop in propiedades:
                    owner_info = prop.get("owner", {})
                    raw_names = owner_info.get("names") or owner_info.get("name") or []
                    
                    if isinstance(raw_names, str):
                        nombre_str = raw_names
                    elif isinstance(raw_names, list) and len(raw_names) > 0:
                        nombre_str = str(raw_names[0])
                    else:
                        nombre_str = ""

                    # Filtrar por apellido latino
                    if nombre_str and nombre_str.strip() and es_apellido_latino(nombre_str):
                        partes = nombre_str.strip().title().split(" ", 1)
                        first_name = partes[0]
                        last_name = partes[1] if len(partes) > 1 else "Propietario"
                        
                        address = prop.get("addressLine1", "")
                        zip_code = prop.get("zipCode", "Desconocido")
                        last_sale = prop.get("lastSale", {})
                        fecha_compra = last_sale.get("date", "") if last_sale else ""

                        if address:
                            lead = {
                                "first_name": first_name,
                                "last_name": last_name,
                                "address": address,
                                "city": prop.get("city", "Houston"),
                                "state": prop.get("state", "TX"),
                                "zip_code": zip_code,
                                "condado": condado,
                                "purchase_date": fecha_compra
                            }

                            if zip_code not in leads_por_zip:
                                leads_por_zip[zip_code] = []
                            leads_por_zip[zip_code].append(lead)

                if len(propiedades) < limit:
                    break
                offset += limit

            except Exception as e:
                print(f"❌ Error durante la extracción de {condado}: {e}")
                break

        # Guardar en disco los archivos organizados por Zip Code
        for zip_code, lista_leads in leads_por_zip.items():
            guardar_csv_por_zip(condado, zip_code, lista_leads)
            
        print(f"✓ Condado {condado} completado con éxito.\n")

if __name__ == "__main__":
    # Ejecución 1: Carga Masiva Inicial (12 meses)
    ejecutar_barrido_rentcast(modo_semanal=False)

    # Para el Cron Job semanal en Render, cambiar a:
    # ejecutar_barrido_rentcast(modo_semanal=True)
