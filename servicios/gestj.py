import socket
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="asistencia",
    user="user",
    password="user"
)
cursor = conn.cursor()

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
            contenido = datos.decode()[5:].strip()
            partes = contenido.split('|')

            if len(partes) == 1:
                rut = partes[0].strip()
                cursor.execute("""
                    SELECT j.id_justificacion, j.fecha, j.motivo
                    FROM JUSTIFICACIONES j
                    JOIN USUARIO u ON j.id_usuario = u.id_usuario
                    WHERE u.rut = %s AND j.estado = 'pendiente'
                    ORDER BY j.fecha;
                """, (rut,))
                filas = cursor.fetchall()

                if not filas:
                    respuesta = "GESTJOKNo hay justificaciones pendientes."
                else:
                    fragmentos = [
                        f"{idj}|{fecha.strftime('%Y-%m-%d')}|{motivo}" for idj, fecha, motivo in filas
                    ]
                    respuesta = "GESTJOK" + ";;".join(fragmentos)

            elif len(partes) == 3:
                id_just, accion, rut = partes
                accion = accion.strip().lower()
                rut = rut.strip()

                if not id_just.isdigit():
                    raise ValueError("ID no es un número entero.")

                id_just = int(id_just)

                if accion not in ['aprobado', 'rechazado']:
                    respuesta = "GESTJNKAcción no válida"
                else:
                    cursor.execute("""
                        SELECT j.estado
                        FROM JUSTIFICACIONES j
                        JOIN USUARIO u ON j.id_usuario = u.id_usuario
                        WHERE j.id_justificacion = %s AND u.rut = %s
                    """, (id_just, rut))
                    result = cursor.fetchone()

                    if not result:
                        respuesta = "GESTJNKJustificación no encontrada o no corresponde al RUT indicado"
                    elif result[0] != 'pendiente':
                        respuesta = f"GESTJNKYa fue gestionada (estado actual: {result[0]})"
                    else:
                        cursor.execute("""
                            UPDATE JUSTIFICACIONES
                            SET estado = %s
                            WHERE id_justificacion = %s
                        """, (accion, id_just))
                        conn.commit()
                        respuesta = f"GESTJOKJustificación {accion} exitosamente"

            else:
                respuesta = "GESTJNKFormato inválido"

        except Exception as e:
            print("Error:", e)
            respuesta = f"GESTJNKError: {str(e)}"

        mensaje_respuesta = f"{len(respuesta):05}{respuesta}"
        print("Enviando respuesta:", mensaje_respuesta)
        sock.sendall(mensaje_respuesta.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
