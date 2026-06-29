import os
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# Mapeo de términos al español basados en tu estructura original
imprimir = print
solicitudes = requests

def ejecutar_extractor():
    imprimir("Iniciando el robot de extracción para Harris County...")
    
    # Configurar el rango de fechas de las últimas 2 semanas (14 días)
    fecha_inicio = (datetime.now() - timedelta(days=14)).strftime('%m/%d/%Y')
    fecha_fin = datetime.now().strftime('%m/%d/%Y')
    
    imprimir(f"Buscando registros desde {fecha_inicio} hasta {fecha_fin}...")

    # URL CORRECTA Y OFICIAL DE TU PROYECTO PUBLICADO
    url_webhook_lovable = "https://name-extract-magic.lovable.app/api/public/leads"

    # Encabezados de seguridad con tu clave API
    encabezados = {
        "Content-Type": "application/json",
        "x-ingest-api-key": "vqpYqSQI5g7YBMvrBZGszxfOWtuYNpwMVyfpNjeDU9V3x_4OrfElT2uVO1kQTMjP"
    }

    with sync_playwright() as p:
        # Lanzar el navegador en modo headless
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        pagina = contexto.new_page()
        
        try:
            # Ir a la página oficial de búsqueda de propiedades de Harris County
            pagina.goto("https://www.hcad.org/property-search")
            pagina.wait_for_timeout(3000) # Esperar a que cargue la interfaz
            
            # --- EXTRACTOR DE DATOS ---
            # Lista de leads de prueba para verificar la inyección inmediata en la base de datos segura:
            leads_extraidos = [
                {
                    "nombre": "John Doe",
                    "direccion": "713 Elm St, Houston, TX 77002",
                    "condado": "Harris",
                    "fecha_registro": fecha_inicio
                },
                {
                    "nombre": "Jane Smith",
                    "direccion": "405 Main St, Houston, TX 77001",
                    "condado": "Harris",
                    "fecha_registro": fecha_fin
                }
            ]
            
            imprimir(f"Se encontró {len(leads_extraidos)} registros nuevos.")
            
            # Enviamos los datos directamente a tu panel de Lovable con la clave de seguridad
            for dirigir in leads_extraidos:
                try:
                    respuesta = solicitudes.post(url_webhook_lovable, json=dirigir, headers=encabezados)
                    if respuesta.status_code in [200, 201]:
                        imprimir(f"Lead enviado con éxito a Lovable: {dirigir['nombre']}")
                    else:
                        imprimir(f"Error al enviar lead. Código de estado: {respuesta.status_code} - Detalle: {respuesta.text}")
                except Exception as e:
                    imprimir(f"Error de conexión con Lovable: {e}")
                    
        except Exception as mi:
            imprimir(f"Ocurrió un error durante la ejecución: {mi}")
        finally:
            navegador.close()

if __name__ == "__main__":
    ejecutar_extractor()
    ejecutar_extractor()
