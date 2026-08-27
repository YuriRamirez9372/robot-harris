import os
import csv
import re
import time
import requests
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SEGURIDAD Y CLIENTES ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
RENTCAST_API_KEY = os.environ.get("11474bdd2ab043929287e5ab0e742115")

# Interruptor de emergencia (si es 'false', apaga todas las llamadas a la API de inmediato)
ENABLE_EXTERNAL_APIS = os.environ.get("ENABLE_EXTERNAL_APIS", "true").lower() == "true"

# Inicializar cliente de Supabase solo si existen credenciales
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None

# --- PARÁMETROS DE BLINDAJE ESTRICTOS ---
MAX_LLAMADAS_DIARIAS = 30     # Cortacircuito global diario (Jamás se cobrarán más de 30 calls/día)
MAX_PETICIONES_POR_RUN = 10   # Máximo de peticiones permitidas por cada ejecución en Render
DELAY_ENTRE_PETICIONES = 2.0  # Pausa de 2 segundos entre solicitudes (evita ráfagas masivas)

# Expresión regular para filtrar apellidos latinos/hispanos
REGEX_APELLIDOS_LATINOS = re.compile(
    r'\b(Garcia|Rodriguez|Martinez|Hernandez|Lopez|Gonzalez|Perez|Sanchez|Ramirez|Torres|Flores|Rivera|Gomez|Diaz|Cruz|Reyes|Morales|Gutierrez|Ortiz|Ramos|Ruiz|Alvarez|Castillo|Mendoza|Moreno|Jimenez|Romero|Herrera|Medina|Aguilar|Vargas|Guzman|Mendez|Munoz|Salazar|Garza|Soto|Vazquez|Cabrera|Campos|Vega|Fuentes|Carrillo|Valdez|Rios|Solis|Pena|Delgado|Valenzuela|Nunez|Zuniga|Cordero|Trevino|Espinosa|Maldonado|Montero|Tinoco|Borges|Suarez)\b', 
    re.IGNORECASE
)

def es_apellido_latino(nombre_completo):
    """Verifica si el nombre contiene patrones latinos."""
    return bool(REGEX_APELLIDOS_LATINOS.search(nombre_completo))

def obtener_llamadas_realizadas_hoy() -> int:
    """Consulta la base de datos de Supabase para saber cuántas llamadas se han ejecutado hoy."""
    if not supabase:
        print("⚠️ Supabase no configurado. Asumiendo límite máximo por precaución.")
        return MAX_LLAMADAS_DIARIAS
    try:
        today_str = time.strftime("%Y-%m-%d")
        res = supabase.table('api_usage_logs') \
            .select('id', count='exact') \
            .eq('provider', 'rentcast') \
            .gte('created_at', f"{today_str}T00:00:00Z") \
            .execute()
        return res.count if res.count is not None else 0
    except Exception as e:
        print(f"⚠️ Error al verificar tabla api_usage_logs. Abortando por seguridad: {e}")
        return MAX_LLAMADAS_DIARIAS

def registrar_log_api(status_code: int):
    """Registra la llamada en la tabla de auditoría inmediatamente."""
    if supabase:
        try:
            supabase.table('api_usage_logs').insert({
                'provider': 'rentcast',
                'endpoint': '/v1/properties',
                'status_code': status_code
            }).execute()
        except Exception as e:
            print(f"⚠️ No se pudo registrar el log de API: {e}")

def guardar_csv_por_zip(condado, zip_code, leads):
    """Crea la estructura de carpetas local y guarda el CSV."""
    directorio = os.path.join("archivos_leads", condado, str(zip_code))
    os.makedirs(directorio, exist_ok=True)
    filepath = os.path.join(directorio, f"leads_{condado}_{zip_code}.csv")
    headers = ["first_name", "last_name", "address", "city", "state", "zip_code", "condado", "purchase_date"]
    
    with open(filepath, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(leads)
        
    print(f"  📁 Lead guardado en disco: {filepath} ({len(leads)} registros)")

def ejecutar_barrido_rentcast(modo_semanal=True):
    # 1. BARRA DE SEGURIDAD: Switch Global
    if not ENABLE_EXTERNAL_APIS:
        print("🛑 ALERTA: 'ENABLE_EXTERNAL_APIS' está desactivado. Extracción abortada.")
        return

    # 2. BARRA DE SEGURIDAD: Auditoría de Límite Diario
    llamadas_hoy = obtener_llamadas_realizadas_hoy()
    print(f"📊 Consumo del día registrado en BD: {llamadas_hoy}/{MAX_LLAMADAS_DIARIAS} llamadas.")

    if llamadas_hoy >= MAX_LLAMADAS_DIARIAS:
        print("🛑 CORTACIRCUITO ACTIVADO: Se alcanzó el máximo de llamadas diarias permitidas.")
        return

    # Calcular cuántas llamadas quedan disponibles para esta ejecución
    cupo_restante = min(MAX_LLAMADAS_DIARIAS - llamadas_hoy, MAX_PETICIONES_POR_RUN)
    peticiones_ejecutadas_run = 0

    dias_rango = "*:7" if modo_semanal else "*:365"
    tipo = "SEMANAL (7 días)" if modo_semanal else "HISTÓRICO (12 meses)"
    print(f"🚀 Iniciando Generación de Leads Blindada | Modo: {tipo} | Cupo disponible: {cupo_restante}\n")
    
    if not RENTCAST_API_KEY:
        print("🔥 ERROR CRÍTICO: RENTCAST_API_KEY no encontrada en las variables de entorno.")
        return

    URL_RENTCAST = "https://api.rentcast.io/v1/properties"
    CONDADOS = ["Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Liberty", "Waller"]
    headers_rentcast = {"X-Api-Key": RENTCAST_API_KEY, "Accept": "application/json"}

    for condado in CONDADOS:
        if peticiones_ejecutadas_run >= cupo_restante:
            print("🛑 Límite de seguridad alcanzado para esta ejecución.")
            break

        print(f"📍 Procesando Condado: {condado} TX...")
        offset = 0
        limit = 10  # Reducido de 500 a 10 para evitar descargas masivas no controladas

        while True:
            # Check de cortacircuito en tiempo real antes de CADA llamada HTTP
            if peticiones_ejecutadas_run >= cupo_restante:
                print("🛑 Deteniendo bucle de peticiones por alcanzar el cupo de seguridad.")
                break

            params = {
                "state": "TX",
                "county": condado,
                "propertyType": "Single Family",
                "saleDateRange": dias_rango,
                "limit": limit,
                "offset": offset
            }

            try:
                # Realizar solicitud a la API
                res = requests.get(URL_RENTCAST, headers=headers_rentcast, params=params, timeout=15)
                peticiones_ejecutadas_run += 1
                
                # Auditoría inmediata en Supabase
                registrar_log_api(res.status_code)
                print(f"Petición #{peticiones_ejecutadas_run}/{cupo_restante} | Condado: {condado} | Status: {res.status_code}")

                if res.status_code != 200:
                    print(f"⚠️ Error {res.status_code} en {condado}: {res.text}")
                    break

                propiedades = res.json()
                if not propiedades:
                    break

                leads_por_zip = {}
                for prop in propiedades:
                    owner_info = prop.get("owner", {})
                    raw_names = owner_info.get("names") or owner_info.get("name") or []
                    
                    if isinstance(raw_names, str):
                        nombre_str = raw_names
                    elif isinstance(raw_names, list) and len(raw_names) > 0:
                        nombre_str = str(raw_names[0])
                    else:
                        nombre_str = ""

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

                            # Guardar en Supabase si la base de datos está disponible
                            if supabase:
                                try:
                                    supabase.table('homeowners').upsert({
                                        'full_name': f"{first_name} {last_name}",
                                        'street_address': address,
                                        'city': lead['city'],
                                        'state': lead['state'],
                                        'zip_code': str(zip_code),
                                        'purchase_date': fecha_compra if fecha_compra else None,
                                        'is_hispanic': True,
                                        'built_year': prop.get("yearBuilt")
                                    }, on_conflict='street_address').execute()
                                except Exception as e_db:
                                    print(f"⚠️ Error al insertar en Supabase: {e_db}")

                            if zip_code not in leads_por_zip:
                                leads_por_zip[zip_code] = []
                            leads_por_zip[zip_code].append(lead)

                # Guardar los registros capturados en archivos CSV locales
                for zip_code, lista_leads in leads_por_zip.items():
                    guardar_csv_por_zip(condado, zip_code, lista_leads)

                if len(propiedades) < limit:
                    break
                offset += limit

            except Exception as e:
                print(f"❌ Error durante la extracción de {condado}: {e}")
                break

            # 3. BARRA DE SEGURIDAD: Pausa obligatoria entre peticiones para prevenir loops agresivos
            time.sleep(DELAY_ENTRE_PETICIONES)

if __name__ == "__main__":
    # Configurado por defecto en modo semanal seguro (7 días)
    ejecutar_barrido_rentcast(modo_semanal=True)
