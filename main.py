import os
import time
import requests

# ==========================================
# CONFIGURACIÓN Y CREDENCIALES
# ==========================================
# Se leen desde las Variables de Railway (o puedes poner los valores directamente entre comillas)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8869156451:AAFQibGkEs54JVhHpgCg_j0QDuLMmGFj-p8")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8295036704")

# Datos de la búsqueda en CABA (SIGECI)
SEDE_ID = "2279"
SERVICIO_ID = "3149"

# Enlace directo de reserva para el usuario
URL_RESERVA = f"https://formulario-sigeci.buenosaires.gob.ar/AgendarTramite?idPrestacion={SERVICIO_ID}"


def enviar_mensaje_telegram(mensaje):
    """Envía una notificación al chat de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")


def consultar_turnos_api():
    """Consulta directamente la API interna de SIGECI para obtener disponibilidad real."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    # API de horas disponibles
    api_url = f"https://formulario-sigeci.buenosaires.gob.ar/getHorasDisp"
    params = {
        "sedeId": SEDE_ID,
        "servicioId": SERVICIO_ID
        # Si se requiere especificar fecha puntual se puede agregar 'day': 'YYYY-MM-DD'
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            try:
                datos = response.json()
            except Exception:
                # Si no devuelve JSON válido pero la respuesta es correcta, analizamos el texto
                datos = response.text

            # Si la respuesta contiene datos/horarios (no está vacía ni es un array vacío '[]')
            if datos and datos != "[]" and datos != []:
                mensaje = (
                    "🔔 <b>¡TURNOS DETECTADOS EN TIEMPO REAL!</b> 🔔\n\n"
                    f"📍 <b>Sede ID:</b> {SEDE_ID}\n"
                    f"🎾 <b>Servicio ID:</b> {SERVICIO_ID}\n\n"
                    f"⏰ <b>Disponibilidad:</b> Se encontraron cupos/horarios habilitados.\n\n"
                    f"🔗 <a href='{URL_RESERVA}'>ENTRAR Y RESERVAR AHORA</a>"
                )
                enviar_mensaje_telegram(mensaje)
                print("¡ALERTA ENVIADA! Horarios detectados en la API.")
            else:
                print("Verificación OK: La API devolvió sin disponibilidad actualmente.")
        else:
            print(f"Error en la consulta a la API: Código {response.status_code}")

    except Exception as e:
        print(f"Error al conectar con la API de SIGECI: {e}")


if __name__ == "__main__":
    print(f"Iniciando monitoreo de API interna para Sede {SEDE_ID} / Servicio {SERVICIO_ID}...")
    
    # Notificación de arranque
    enviar_mensaje_telegram(
        f"🚀 <b>Bot Activo:</b> Monitoreando la API interna de turnos (Sede {SEDE_ID}) cada 5 minutos."
    )

    while True:
        consultar_turnos_api()
        time.sleep(300)  # Revisa cada 5 minutos
