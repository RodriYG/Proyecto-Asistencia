import socket
import psycopg2

# Conexión a la base de datos
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="asistencia",
    user="user",
    password="user"
)
cursor = conn.cursor()

# Conexión al bus
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
bus_address = ('localhost', 5000)
print('Conectando al bus en {}:{}'.format(*bus_address))
sock.connect(bus_address)

mensaje_sinit = b'00010sinitGESTJ'
print('Enviando sinit:', mensaje_sinit)
sock.sendall(mensaje_sinit)
sinit = True

try:
    while True:
        print("Esperando transacción...")
        largo = int(sock.recv(5))
        datos = sock.recv(largo)
        print("Recibido:", datos)

        if sinit:
            sinit = False
            print("sinit recibido")
            continue

        try:
            contenido = datos.decode().strip()
            print("Contenido recibido:", contenido)

            if not contenido.startswith("GESTJ"):
                raise ValueError("Prefijo inválido (se esperaba GESTJ).")

            contenido = contenido[5:].strip()
            partes = contenido.split('|')

            # --- Consulta de justificaciones pendientes ---
            if len(partes) == 1:
                rut = partes[0].strip()

                if not rut or not rut.isdigit():
                    raise ValueError("El RUT debe contener solo números.")

                cursor.execute("""
                    SELECT j.id_justificacion, j.fecha, j.motivo
                    FROM JUSTIFICACIONES j
                    JOIN USUARIO u ON j.id_usuario = u.id_usuario
                    WHERE u.rut = %s AND j.estado = 'pendiente'
                    ORDER BY j.fecha;
                """, (rut,))
                filas = cursor.fetchall()

                if not filas:
                    respuesta = "GESTJOKNo hay justificaciones pendientes para este usuario."
                else:
                    fragmentos = [
                        f"{idj}|{fecha.strftime('%Y-%m-%d')}|{motivo}" for idj, fecha, motivo in filas
                    ]
                    respuesta = "GESTJOK" + ";;".join(fragmentos)

            # --- Gestión de una justificación (aprobado/rechazado) ---
            elif len(partes) == 3:
                id_just, accion, rut = [p.strip() for p in partes]
                accion = accion.lower()

                if not id_just.isdigit():
                    raise ValueError("ID debe ser un número entero.")
                if not rut.isdigit():
                    raise ValueError("El RUT debe contener solo números.")
                if accion not in ['aprobado', 'rechazado']:
                    raise ValueError("Acción no válida. Debe ser 'aprobado' o 'rechazado'.")

                id_just = int(id_just)

                cursor.execute("""
                    SELECT j.estado
                    FROM JUSTIFICACIONES j
                    JOIN USUARIO u ON j.id_usuario = u.id_usuario
                    WHERE j.id_justificacion = %s AND u.rut = %s
                """, (id_just, rut))
                result = cursor.fetchone()

                if not result:
                    respuesta = "GESTJNKJustificación no encontrada o no corresponde al RUT indicado."
                elif result[0] != 'pendiente':
                    respuesta = f"GESTJNKYa fue gestionada (estado actual: {result[0]})."
                else:
                    cursor.execute("""
                        UPDATE JUSTIFICACIONES
                        SET estado = %s
                        WHERE id_justificacion = %s
                    """, (accion, id_just))
                    conn.commit()
                    respuesta = f"GESTJOKJustificación {accion} exitosamente."

            else:
                raise ValueError("Formato inválido. Se esperaban 1 o 3 campos.")

        except Exception as e:
            conn.rollback()
            print("Error:", e)
            respuesta = f"GESTJNKError: {str(e)}"

        mensaje_respuesta = f"{len(respuesta):05}{respuesta}"
        print("Enviando respuesta:", mensaje_respuesta)
        sock.sendall(mensaje_respuesta.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
