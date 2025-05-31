import socket
import psycopg2
from datetime import datetime

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

mensaje_sinit = b'00010sinitJUSTI'
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
            rut, fecha_str, motivo = contenido.split('|')
            rut = int(rut.strip())
            fecha = datetime.strptime(fecha_str.strip(), '%Y-%m-%d').date()
            fecha_solicitud = datetime.now()

            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            user = cursor.fetchone()

            if not user:
                respuesta = "JUSTINKUsuario no encontrado"
            else:
                id_usuario = user[0]
                cursor.execute("""
                    INSERT INTO JUSTIFICACIONES (id_usuario, fecha, motivo, estado, fecha_solicitud)
                    VALUES (%s, %s, %s, 'pendiente', %s)
                """, (id_usuario, fecha, motivo, fecha_solicitud))
                conn.commit()
                respuesta = "JUSTIOKJustificación registrada como pendiente"

        except Exception as e:
            print("Error:", e)
            respuesta = f"JUSTINKError: {str(e)}"

        mensaje_respuesta = f"{len(respuesta):05}{respuesta}"
        print("Enviando respuesta:", mensaje_respuesta)
        sock.sendall(mensaje_respuesta.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
