import os
import time
import requests
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN Y CREDENCIALES
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8869156451:AAFQibGkEs54JVhHpgCg_j0QDuLMmGFj-p8")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8295036704")

# Datos de la búsqueda en CABA (SIGECI)
SEDE_ID = "2279"
SERVICIO_ID = "3149"
DIAS_A_CONSULTAR = 30  # Revisa los próximos 30 días

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
    """Consulta la API de SIGECI recorriendo un rango de fechas futuras."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    hoy = datetime.now()
    turnos_encontrados = []

    # Recorremos los próximos N días
    for i in range(DIAS_A_CONSULTAR):
        fecha_str = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")

        api_url = "https://formulario-sigeci.buenosaires.gob.ar/getHorasDisp"
        params = {
            "day": fecha_str,
            "sedeId": SEDE_ID,
            "servicioId": SERVICIO_ID
        }

        try:
            response = requests.get(api_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                try:
                    datos = response.json()
                except Exception:
                    datos = response.text

                # Si la API devuelve un listado válido con datos
                if datos and datos != "[]" and datos != []:
                    print(f"¡Atención! Turno encontrado para el día {fecha_str}: {datos}")
                    turnos_encontrados.append(f"📅 <b>{fecha_str}:</b> {datos}")

        except Exception as e:
            print(f"Error consultando fecha {fecha_str}: {e}")

        # Pausa ligera entre llamadas para no saturar la API
        time.sleep(0.3)

    # Si se encontraron turnos en alguna de las fechas del rango
    if turnos_encontrados:
        resumen_turnos = "\n".join(turnos_encontrados)
        mensaje = (
            "🔔 <b>¡TURNOS DETECTADOS EN CABA!</b> 🔔\n\n"
            f"📍 <b>Sede ID:</b> {SEDE_ID}\n"
            f"🎾 <b>Servicio ID:</b> {SERVICIO_ID}\n\n"
            f"<b>Disponibilidad encontrada:</b>\n{resumen_turnos}\n\n"
            f"🔗 <a href='{URL_RESERVA}'>RESERVAR AHORA EN SIGECI</a>"
        )
        enviar_mensaje_telegram(mensaje)
        print("¡ALERTA ENVIADA! Notificación enviada a Telegram.")
    else:
        print(f"Verificación OK: Sin disponibilidad en los próximos {DIAS_A_CONSULTAR} días.")


if __name__ == "__main__":
    print(f"Iniciando monitoreo de API con barrido de {DIAS_A_CONSULTAR} días...")

    enviar_mensaje_telegram(
        f"🚀 <b>Bot Activo:</b> Monitoreando los próximos {DIAS_A_CONSULTAR} días cada 5 minutos."
    )

    while True:
        consultar_turnos_api()
        time.sleep(300)  # Espera 5 minutos entre barridos
