from pyrfc import Connection
from gen_ai_hub.orchestration.models.tool import function_tool

# Decoramos la función para registrarla como herramienta en la orquestación
@function_tool()
def actualizar_notificacion(notif_id: str,
                            puesto_trabajo: str,
                            clase_act: str,
                            fecha_contab: str,
                            trabajo_real: float,
                            inicio: str,
                            fin: str) -> str:
    """
    Actualiza una notificación de orden de mantenimiento en SAP.
    notif_id: número de notificación
    puesto_trabajo: código del puesto de trabajo
    clase_act: clase de actividad
    fecha_contab: fecha de contabilización (YYYYMMDD)
    trabajo_real: horas de trabajo real
    inicio: fecha/hora de inicio (YYYYMMDDHHMM)
    fin: fecha/hora de fin (YYYYMMDDHHMM)
    """
    # Establecer conexión (usar parámetros de conexión de SAP)
    conn = Connection(ashost='hostname', sysnr='00',
                      client='100', user='USER', passwd='PASSWORD')

    # Preparar estructura para BAPI_ALM_NOTIF_PUT (ejemplo)
    input_data = {
        'NOTIFHEADER': {
            'NOTIF_NO': notif_id,
            'WORK_CNTR': puesto_trabajo,
            'CATPROFILE': clase_act,
            'QTYSAM_WRK': trabajo_real,
            'POSTG_DATE': fecha_contab,
        },
        'NOTIFTASK': {
            # Estructura de tareas, si aplica
        },
        # Otras tablas o estructuras según la BAPI usada
    }

    result = conn.call('BAPI_ALM_NOTIF_PUT', **input_data)

    # Confirmar la actualización (BAPI commit)
    conn.call('BAPI_TRANSACTION_COMMIT')
    return f"Notificación {notif_id} actualizada"