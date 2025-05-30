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

# Conexión al bus SOA
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
bus_address = ('localhost', 5000)
print("Conectando al bus en {}:{}".format(*bus_address))
sock.connect(bus_address)

# Registro del servicio en el bus
mensaje_sinit = b'00010sinitMASIS'
sock.sendall(mensaje_sinit)
sinit = True

try:
    while True:
        print("Esperando transacción...")
        largo = int(sock.recv(5))
        datos = sock.recv(largo)
        print("Datos recibidos:", datos)

        if sinit:
            sinit = False
            print("Respuesta sinit recibida.")
            continue

        try:
            rut = int(datos.decode()[5:].strip())
            hoy = datetime.now().date()
            hora = datetime.now().time()

            # Buscar el id_usuario correspondiente al rut
            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            usuario = cursor.fetchone()

            if not usuario:
                respuesta = "MASISNKRut no registrado"
            else:
                id_usuario = usuario[0]

                # Verificar si ya hay asistencia hoy
                cursor.execute("""
                    SELECT * FROM ASISTENCIAS
                    WHERE id_usuario = %s AND fecha = %s
                """, (id_usuario, hoy))
                existente = cursor.fetchone()

                if existente:
                    respuesta = "MASISNKYa se registró asistencia hoy"
                else:
                    cursor.execute("""
                        INSERT INTO ASISTENCIAS (id_usuario, fecha, hora_entrada)
                        VALUES (%s, %s, %s)
                    """, (id_usuario, hoy, hora))
                    conn.commit()
                    respuesta = "MASISOKAsistencia registrada correctamente"

        except Exception as e:
            print("Error:", e)
            respuesta = f"MASISNKError: {str(e)}"

        mensaje_respuesta = f"{len(respuesta):05}{respuesta}"
        sock.sendall(mensaje_respuesta.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
