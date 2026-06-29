import os
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

imprimir = print
solicitudes = requests

def ejecutar_extractor():
    imprimir("Iniciando el robot de extracción para Harris County...")
    
    fecha_inicio = (datetime.now() - timedelta(days=14)).strftime('%m/%d/%Y')
    fecha_fin = datetime.now().strftime('%m/%d/%Y')
    
    imprimir(f"Buscando registros desde {fecha_inicio} hasta {fecha_fin}...")

    url_webhook_lovable = "https://project--543227ce-de86-45d8-b9b6-969bc7396a1c.lovable.app/api/public/leads"

    encabezados = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        pagina = contexto.new_page()
        
        try:
            pagina.goto("https://www.hcad.org/property-search")
            pagina.wait_for_timeout(3000)
            
            # DATOS DE PRUEBA CORREGIDOS (Sin user_id para que Lovable lo asigne automáticamente)
            lista_leads = [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "direccion": "713 Elm St",
                    "city": "Houston",
                    "state": "TX",
                    "zip_code": "77002",
                    "condado": "Harris",
                    "fecha_registro": fecha_inicio
                }
            ]
            
            imprimir(f"Se encontró {len(lista_leads)} registros nuevos.")
            
            paquete_datos = {
                "leads": lista_leads
            }
            
            try:
                respuesta = solicitudes.post(url_webhook_lovable, json=paquete_datos, headers=encabezados)
                if respuesta.status_code in [200, 201]:
                    imprimir("¡Paquete de leads enviado con éxito total a Lovable!")
                else:
                    imprimir(f"Error al enviar paquete. Código de estado: {respuesta.status_code} - Detalle: {respuesta.text}")
            except Exception as e:
                imprimir(f"Error de conexión con Lovable: {e}")
                    
        except Exception as mi:
            imprimir(f"Ocurrió un error durante la ejecución: {mi}")
        finally:
            navegador.close()

if __name__ == "__main__":
    ejecutar_extractor()
