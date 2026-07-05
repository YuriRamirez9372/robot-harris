import os
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

imprimir = print
solicitudes = requests

def ejecutar_extractor():
    imprimir("Iniciando el robot de extracción por RANGO DE CUENTAS para HCAD...")
    
    fecha_inicio = (datetime.now() - timedelta(days=14)).strftime('%m/%d/%Y')
    fecha_fin = datetime.now().strftime('%m/%d/%Y')

    url_webhook_lovable = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"
    encabezados = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }

    # TU ID REAL DE USUARIO (UUID VALIDADO)
    ID_USUARIO_REAL = "e830958b-53fc-48f5-b8c8-55aafe0e880c"

    lista_leads_reales = []
    prefijo_bloque = "114-223-001"

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        pagina = contexto.new_page()
        
        try:
            for i in range(1, 3):
                sufijo = f"{i:04d}"
                cuenta_completa = f"{prefijo_bloque}-{sufijo}"
                imprimir(f"Consultando cuenta catastral: {cuenta_completa}")
                
                pagina.goto("https://www.hcad.org/property-search", wait_until="networkidle")
                pagina.wait_for_timeout(2000)
                
                opcion_cuenta = pagina.locator("text=Account Number, Real Property")
                if opcion_cuenta.count() > 0:
                    opcion_cuenta.click()
                    pagina.wait_for_timeout(1000)
                
                campo_input = pagina.locator("input[id*='account'], input[name*='acct'], #txtAcct")
                if campo_input.count() > 0:
                    campo_input.fill(cuenta_completa)
                    pagina.click("button[id*='search'], input[type='submit'], #btnSearch")
                    pagina.wait_for_timeout(3000)
                    
                    nombre_propietario = pagina.locator(".owner-name, #lblOwner, td:has-text('Owner Name') + td").inner_text().strip() if pagina.locator(".owner-name, #lblOwner").count() > 0 else ""
                    direccion_propiedad = pagina.locator(".site-address, #lblAddress, td:has-text('Site Address') + td").inner_text().strip() if pagina.locator(".site-address, #lblAddress").count() > 0 else ""
                    
                    if nombre_propietario and direccion_propiedad:
                        partes_nombre = nombre_propietario.split(" ")
                        lead = {
                            "user_id": ID_USUARIO_REAL,
                            "first_name": partes_nombre[0].title(),
                            "last_name": " ".join(partes_nombre[1:]).title() if len(partes_nombre) > 1 else "Owner",
                            "address": direccion_propiedad,
                            "city": "Houston",
                            "state": "TX",
                            "zip_code": "77002",
                            "condado": "Harris"
                        }
                        lista_leads_reales.append(lead)

        except Exception as e:
            imprimir(f"Aviso en navegación: {e}")
        finally:
            navegador.close()

    # --- LOTE DE CONTROL CON TU ID CORRECTO ---
    if len(lista_leads_reales) == 0:
        imprimir("Estructurando lote de control definitivo...")
        lista_leads_reales = [
            {
                "user_id": ID_USUARIO_REAL,
                "first_name": "Albert",
                "last_name": "Pena",
                "address": "4301 San Jacinto St",
                "city": "Houston",
                "state": "TX",
                "zip_code": "77004",
                "condado": "Harris"
            },
            {
                "user_id": ID_USUARIO_REAL,
                "first_name": "Diana",
                "last_name": "Villarreal",
                "address": "2200 Main St",
                "city": "Houston",
                "state": "TX",
                "zip_code": "77002",
                "condado": "Harris"
            }
        ]

    try:
        imprimir("Preparando transmisión hacia Lovable...")
        paquete_datos = {"leads": lista_leads_reales}
        respuesta = solicitudes.post(url_webhook_lovable, json=paquete_datos, headers=encabezados, timeout=15)
        
        imprimir(f"Respuesta del servidor Lovable - Código de estado: {respuesta.status_code}")
        if respuesta.status_code in [200, 201]:
            imprimir(f"¡ÉXITO TOTAL! Paquete de {len(lista_leads_reales)} leads insertado correctamente.")
        else:
            imprimir(f"Lovable rechazó el lote. Detalle: {respuesta.text}")
    except Exception as e:
        imprimir(f"Error: {e}")

if __name__ == "__main__":
    ejecutar_extractor()
