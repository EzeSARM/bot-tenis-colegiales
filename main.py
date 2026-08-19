import os
import time
import requests
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN Y CREDENCIALES - COLEGIALES
# ==========================================
TELEGRAM_TOKEN = "8869156451:AAFQibGkEs54JVhHpgCg_j0QDuLMmGFj-p8"
TELEGRAM_CHAT_ID = "8295036704"

NOMBRE_POLIDEPORTIVO = "Polideportivo Colegiales"
SERVICIO_ID = "3149"

# Configuración de las dos canchas con sus respectivos sedeId
CANCHAS = [
    {"nombre": "Cancha 1", "sede_id": "2263"},
    {"nombre": "Cancha 2", "sede_id": "2279"}
]

DIAS_A_CONSULTAR = 30
TURNOS_NOTIFICADOS = set()

DIAS_SEMANA = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}


def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje a Telegram en formato HTML."""
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN.startswith("COLOCA_AQUI"):
        print("❌ Error: Debes ingresar tu TELEGRAM_TOKEN en el archivo main.py.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")
        return False


def crear_sesion_sigeci():
    """Inicializa la sesión HTTP para obtener la cookie PHPSESSID legítima."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://formulario-sigeci.buenosaires.gob.ar/AgendarTramite?idPrestacion={SERVICIO_ID}&flow=primeros"
    })
    
    url_inicio = f"https://formulario-sigeci.buenosaires.gob.ar/AgendarTramite?idPrestacion={SERVICIO_ID}&flow=primeros"
    try:
        session.get(url_inicio, timeout=10)
    except Exception as e:
        print(f"⚠️ Aviso inicializando sesión: {e}")
        
    return session


def extraer_horas_validas(lista_datos):
    """Extrae y limpia los horarios reales devueltos por la API."""
    horas_validas = []
    if not isinstance(lista_datos, list):
        return horas_validas

    for item in lista_datos:
        if not isinstance(item, str):
            continue

        item_str = item.strip()

        if "T" in item_str:
            try:
                dt_hora = datetime.strptime(item_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                horas_validas.append(dt_hora.strftime("%H:%M hs"))
            except ValueError:
                pass
        elif ":" in item_str and len(item_str) <= 8:
            try:
                partes = item_str.split(":")
                hora_str = f"{int(partes[0]):02d}:{int(partes[1]):02d} hs"
                horas_validas.append(hora_str)
            except ValueError:
                pass

    return sorted(list(set(horas_validas)))


def consultar_cancha(cancha_info):
    global TURNOS_NOTIFICADOS

    nombre_cancha = cancha_info["nombre"]
    sede_id = cancha_info["sede_id"]

    session = crear_sesion_sigeci()
    url_reserva = f"https://formulario-sigeci.buenosaires.gob.ar/AgendarTramite?idPrestacion={SERVICIO_ID}"

    hoy = datetime.now()
    lineas_resumen = []
    turnos_nuevos_detectados = []
    turnos_visibles_hoy = set()
    hay_turnos_reales = False

    for i in range(DIAS_A_CONSULTAR):
        fecha_str = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")

        api_url = "https://formulario-sigeci.buenosaires.gob.ar/getHorasDisp"
        params = {
            "day": fecha_str,
            "sedeId": sede_id,
            "servicioId": SERVICIO_ID
        }

        try:
            response = session.get(api_url, params=params, timeout=8)

            if response.status_code == 200:
                try:
                    datos = response.json()
                except Exception:
                    datos = []

                if datos and isinstance(datos, list):
                    horas_limpias = extraer_horas_validas(datos)

                    if horas_limpias:
                        hay_turnos_reales = True
                        try:
                            dt_fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                            dia_nombre = DIAS_SEMANA.get(dt_fecha.strftime("%A"), dt_fecha.strftime("%A"))
                            fecha_corta = dt_fecha.strftime("%d/%m")
                            texto_linea = f"📅 <b>{dia_nombre} {fecha_corta}:</b> {', '.join(horas_limpias)}"
                        except Exception:
                            texto_linea = f"📅 <b>{fecha_str}:</b> {', '.join(horas_limpias)}"

                        for h in horas_limpias:
                            clave_unica = f"{sede_id}|{fecha_str}|{h}"
                            turnos_visibles_hoy.add(clave_unica)

                            if clave_unica not in TURNOS_NOTIFICADOS:
                                turnos_nuevos_detectados.append(clave_unica)

                        lineas_resumen.append(texto_linea)
        except Exception:
            pass

        time.sleep(0.05)

    # Limpiar memoria de turnos antiguos que ya no están disponibles para esta sede
    turnos_a_remover = [
        t for t in TURNOS_NOTIFICADOS 
        if t.startswith(f"{sede_id}|") and t not in turnos_visibles_hoy
    ]
    for t in turnos_a_remover:
        TURNOS_NOTIFICADOS.remove(t)

    # Notificación a Telegram
    if turnos_nuevos_detectados:
        resumen_turnos = "\n".join(lineas_resumen)
        mensaje = (
            "🔔 <b>¡NUEVO TURNO DISPONIBLE EN CABA!</b> 🔔\n\n"
            f"📍 <b>Lugar:</b> {NOMBRE_POLIDEPORTIVO}\n"
            f"🎾 <b>Cancha:</b> {nombre_cancha}\n\n"
            f"<b>Disponibilidad encontrada:</b>\n{resumen_turnos}\n\n"
            f"🔗 <a href='{url_reserva}'>RESERVAR AHORA EN SIGECI</a>"
        )
        if enviar_mensaje_telegram(mensaje):
            for t in turnos_nuevos_detectados:
                TURNOS_NOTIFICADOS.add(t)
            print(f"✅ ALERTA ENVIADA: {len(turnos_nuevos_detectados)} turnos nuevos en {nombre_cancha}.")
    elif hay_turnos_reales:
        print(f"ℹ️ {nombre_cancha} (Sede {sede_id}): Hay turnos libres pero ya fueron notificados.")
    else:
        print(f"ℹ️ {nombre_cancha} (Sede {sede_id}): Sin disponibilidad real.")


if __name__ == "__main__":
    print(f"🚀 Iniciando monitoreo de Cancha 1 y Cancha 2 en {NOMBRE_POLIDEPORTIVO}...")

    enviar_mensaje_telegram(
        f"🚀 <b>Bot Activo:</b> Monitoreando Cancha 1 y Cancha 2 en {NOMBRE_POLIDEPORTIVO}."
    )

    while True:
        try:
            for cancha in CANCHAS:
                consultar_cancha(cancha)
                time.sleep(0.5)
        except Exception as main_e:
            print(f"❌ Error en el bucle principal: {main_e}")

        time.sleep(300)
