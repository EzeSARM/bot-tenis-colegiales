import os
import time
import requests
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN Y CREDENCIALES
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8869156451:AAFQibGkEs54JVhHpgCg_j0QDuLMmGFj-p8")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8295036704")

SEDE_ID = "2279"  # Polideportivo Colegiales
DIAS_A_CONSULTAR = 30  # Revisa los próximos 30 días

# CONFIGURACIÓN DE CANCHAS (Agrega aquí los IDs reales de cada cancha)
CANCHAS = [
    {
        "nombre": "Cancha 1",
        "servicio_id": "3149",
        "url": "https://formulario-sigeci.buenosaires.gob.ar/AgendarTramite?idPrestacion=3149"
    },
    {
        "nombre": "Cancha 2",
        "servicio_id": "3150",  # Reemplaza 3150 por el ID real de la Cancha 2
        "url": "https://formulario-sigeci.buenosaires.gob.ar/AgendarTramite?idPrestacion=3150"
    }
]

DIAS_SEMANA = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}


def formatear_horarios(fecha_str, lista_iso):
    """Convierte la fecha y lista de horas ISO en texto claro."""
    try:
        dt_fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        dia_nombre = DIAS_SEMANA.get(dt_fecha.strftime("%A"), dt_fecha.strftime("%A"))
        fecha_corta = dt_fecha.strftime("%d/%m")

        horas_limpias = []
        for item in lista_iso:
            try:
                dt_hora = datetime.strptime(item.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                horas_limpias.append(dt_hora.strftime("%H:%M hs"))
            except Exception:
                horas_limpias.append(str(item))

        return f"📅 <b>{dia_nombre} {fecha_corta}:</b> {', '.join(horas_limpias)}"
    except Exception:
        return f"📅 <b>{fecha_str}:</b> {lista_iso}"


def enviar_mensaje_telegram(mensaje):
    """Envía una notificación al chat de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")


def consultar_cancha(cancha):
    """Consulta la API de SIGECI para una cancha específica en los próximos N días."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    hoy = datetime.now()
    turnos_encontrados = []

    for i in range(DIAS_A_CONSULTAR):
        fecha_str = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")

        api_url = "https://formulario-sigeci.buenosaires.gob.ar/getHorasDisp"
        params = {
            "day": fecha_str,
            "sedeId": SEDE_ID,
            "servicioId": cancha["servicio_id"]
        }

        try:
            response = requests.get(api_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                try:
                    datos = response.json()
                except Exception:
                    datos = []

                if datos and isinstance(datos, list) and len(datos) > 0:
                    linea_formateada = formatear_horarios(fecha_str, datos)
                    turnos_encontrados.append(linea_formateada)

        except Exception as e:
            print(f"Error consultando {cancha['nombre']} para el día {fecha_str}: {e}")

        time.sleep(0.2)

    if turnos_encontrados:
        resumen_turnos = "\n".join(turnos_encontrados)
        mensaje = (
            "🔔 <b>¡TURNO DISPONIBLE EN CABA!</b> 🔔\n\n"
            f"📍 <b>Lugar:</b> Polideportivo Colegiales\n"
            f"🎾 <b>Cancha:</b> {cancha['nombre']}\n\n"
            f"<b>Disponibilidad encontrada:</b>\n{resumen_turnos}\n\n"
            f"🔗 <a href='{cancha['url']}'>RESERVAR AHORA EN SIGECI</a>"
        )
        enviar_mensaje_telegram(mensaje)
        print(f"¡ALERTA ENVIADA! Turno disponible en {cancha['nombre']}.")
    else:
        print(f"Verificación OK: Sin disponibilidad en {cancha['nombre']}.")


if __name__ == "__main__":
    nombres_canchas = ", ".join([c["nombre"] for c in CANCHAS])
    print(f"Iniciando monitoreo de Colegiales para: {nombres_canchas}...")

    enviar_mensaje_telegram(
        f"🚀 <b>Bot Activo:</b> Monitoreando {nombres_canchas} en Polideportivo Colegiales cada 5 minutos."
    )

    while True:
        for cancha in CANCHAS:
            consultar_cancha(cancha)
            time.sleep(1)  # Pausa breve entre canchas

        time.sleep(300)  # Espera 5 minutos antes del próximo ciclo completo
