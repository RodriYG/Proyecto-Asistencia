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

mensaje_sinit = b'00010sinitMASIS'
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

        correo = datos.decode()[5:].strip()
        print("Correo recibido:", correo)

        now = datetime.now()
        fecha = now.date()
        hora = now.strftime('%H:%M:%S')

        try:
            cursor.execute("SELECT id_usuario FROM USUARIO WHERE email = %s", (correo,))
            user = cursor.fetchone()

            if not user:
                respuesta = "MASISNKUsuario no encontrado"
            else:
                id_usuario = user[0]

                cursor.execute("""
                    SELECT id_asistencia, hora_entrada, hora_salida
                    FROM ASISTENCIAS
                    WHERE id_usuario = %s AND fecha = %s
                    ORDER BY id_asistencia DESC
                    LIMIT 1
                """, (id_usuario, fecha))
                asistencia = cursor.fetchone()

                if not asistencia:
                    cursor.execute("""
                        INSERT INTO ASISTENCIAS (id_usuario, fecha, hora_entrada)
                        VALUES (%s, %s, %s)
                    """, (id_usuario, fecha, hora))
                    conn.commit()
                    respuesta = "MASISOKEntrada registrada correctamente"
                elif asistencia[2] is None:
                    cursor.execute("""
                        UPDATE ASISTENCIAS
                        SET hora_salida = %s
                        WHERE id_asistencia = %s
                    """, (hora, asistencia[0]))
                    conn.commit()
                    respuesta = "MASISOKSalida registrada correctamente"
                else:
                    respuesta = "MASISOKYa registraste entrada y salida hoy"

        except Exception as e:
            print("Error:", e)
            respuesta = f"MASISNKError: {str(e)}"

        mensaje_respuesta = f"{len(respuesta):05}{respuesta}"
        print("Enviando respuesta:", mensaje_respuesta)
        sock.sendall(mensaje_respuesta.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
