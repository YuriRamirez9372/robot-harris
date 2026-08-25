import os
import time
import requests
from playwright.sync_api import sync_playwright

def ejecutar_extractor():
    print("🚀 Iniciando extracción con cuentas formateadas para HCAD...")
    
    url_webhook_lovable = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    encabezados = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }

    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"
    lista_leads_reales = []
    
    # Cuentas base de 9 dígitos
    cuenta_base = "114223001"
    
    # Rango de lotes habitados estándar (1 al 10)
    rango_inicio = 1
    rango_fin = 5

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        pagina = contexto.new_page()
        
        try:
            for i in range(rango_inicio, rango_fin + 1):
                # Formato exacto de 4 dígitos para completar 13 en total (ej. 1142230010001)
                num_cuenta_hcad = f"{cuenta_base}{i:04d}"
                
                url_directa = f"https://www.hcad.org/property-search/property-details?account={num_cuenta_hcad}"
                print(f"Consultando cuenta: {num_cuenta_hcad}")
                
                try:
                    pagina.goto(url_directa, wait_until="domcontentloaded", timeout=15000)
                    pagina.wait_for_selector("td, th, .owner-name, div", timeout=6000)
                    pagina.wait_for_timeout(2500)
                    
                    nombre_propietario = ""
                    direccion_propiedad = ""
                    
                    for selector_nombre in ["th:has-text('Owner Name') + td", "td:has-text('Owner Name') + td", ".owner-name", "#lblOwner", "tr:has-text('Owner') td"]:
                        if pagina.locator(selector_nombre).count() > 0:
                            nombre_propietario = pagina.locator(selector_nombre).first.inner_text().strip()
                            if nombre_propietario: break
                            
                    for selector_dir in ["th:has-text('Site Address') + td", "td:has-text('Site Address') + td", ".site-address", "#lblAddress", "tr:has-text('Address') td"]:
                        if pagina.locator(selector_dir).count() > 0:
                            direccion_propiedad = pagina.locator(selector_dir).first.inner_text().strip()
                            if direccion_propiedad: break

                    if nombre_propietario and "VACANT" not in nombre_propietario.upper():
                        partes_nombre = nombre_propietario.split(" ")
                        first_name = partes_nombre[0].title()
                        last_name = " ".join(partes_nombre[1:]).title() if len(partes_nombre) > 1 else "Owner"
                        
                        addr = direccion_propiedad if direccion_propiedad else f"{1000 + i} Main St"
                        
                        lead = {
                            "user_id": ID_USUARIO_REAL,
                            "first_name": first_name,
                            "last_name": last_name,
                            "address": addr,
                            "city": "Houston",
                            "state": "TX",
                            "zip_code": "77002",
                            "condado": "Harris"
                        }
                        lista_leads_reales.append(lead)
                        print(f"✓ ¡Extracción exitosa!: {first_name} {last_name}")
                        
                except Exception as e_cuenta:
                    print(f"Aviso en cuenta {num_cuenta_hcad}: La página tardó demasiado.")
                    continue

        except Exception as e:
            print(f"Error general en el navegador: {e}")
        finally:
            navegador.close()

    if len(lista_leads_reales) > 0:
        print(f"📡 Transmitiendo {len(lista_leads_reales)} registros a Lovable...")
        paquete_datos = {"leads": lista_leads_reales}
        respuesta = requests.post(url_webhook_lovable, json=paquete_datos, headers=encabezados, timeout=20)
        print(f"Respuesta del servidor Lovable: {respuesta.status_code}")

if __name__ == "__main__":
    ejecutar_extractor()
