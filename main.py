import os
import time
import requests
from datetime import datetime

# ==========================================
# CONFIGURACIÓN Y CREDENCIALES
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8869156451:AAFQibGkEs54JVhHpgCg_j0QDuLMmGFj-p8")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8295036704")

# Datos de la búsqueda en CABA (SIGECI)
SEDE_ID = "2279"
SERVICIO_ID = "3149"

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
    """Consulta la API interna de SIGECI enviando la fecha obligatoria."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Fecha de hoy en formato YYYY-MM-DD
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    api_url = "https://formulario-sigeci.buenosaires.gob.ar/getHorasDisp"
    params = {
        "day": fecha_hoy,
        "sedeId": SEDE_ID,
        "servicioId": SERVICIO_ID
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            try:
                datos = response.json()
            except Exception:
                datos = response.text

            # Si la API devuelve un listado con horas (no vacío)
            if datos and datos != "[]" and datos != []:
                mensaje = (
                    "🔔 <b>¡TURNOS DETECTADOS EN TIEMPO REAL!</b> 🔔\n\n"
                    f"📅 <b>Fecha consultada:</b> {fecha_hoy}\n"
                    f"📍 <b>Sede ID:</b> {SEDE_ID}\n"
                    f"🎾 <b>Servicio ID:</b> {SERVICIO_ID}\n\n"
                    f"⏰ <b>Horarios encontrados:</b> {datos}\n\n"
                    f"🔗 <a href='{URL_RESERVA}'>ENTRAR Y RESERVAR AHORA</a>"
                )
                enviar_mensaje_telegram(mensaje)
                print("¡ALERTA ENVIADA! Horarios detectados.")
            else:
                print(f"Verificación OK ({fecha_hoy}): Sin disponibilidad actual.")
        else:
            print(f"Error en la consulta a la API: Código {response.status_code}")

    except Exception as e:
        print(f"Error al conectar con la API de SIGECI: {e}")


if __name__ == "__main__":
    print(f"Iniciando monitoreo de API para Sede {SEDE_ID} / Servicio {SERVICIO_ID}...")
    
    enviar_mensaje_telegram(
        f"🚀 <b>Bot Activo:</b> Monitoreando la API interna de turnos (Sede {SEDE_ID}) cada 5 minutos."
    )

    while True:
        consultar_turnos_api()
        time.sleep(300)
