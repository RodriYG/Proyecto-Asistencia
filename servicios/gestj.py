import socket
import psycopg2

# Conexión a PostgreSQL
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
            id_just, accion = contenido.split('|')
            id_just = int(id_just)
            accion = accion.strip().lower()

            if accion not in ['aprobado', 'rechazado']:
                respuesta = "GESTJNKAcción no válida"
            else:
                cursor.execute("SELECT estado FROM JUSTIFICACIONES WHERE id_justificacion = %s", (id_just,))
                result = cursor.fetchone()
                if not result:
                    respuesta = "GESTJNKJustificación no encontrada"
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
