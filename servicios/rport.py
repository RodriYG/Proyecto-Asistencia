import json
import psycopg2
from datetime import datetime
import socket

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
print("Conectando a bus:", bus_address)
sock.connect(bus_address)

sinit = b'00010sinitRPORT'
print("Enviando sinit:", sinit)
sock.sendall(sinit)
esperando_sinit = True

try:
    while True:
        print("Esperando transacción...")
        largo = int(sock.recv(5))
        data = sock.recv(largo)
        print("Recibido:", data)

        if esperando_sinit:
            esperando_sinit = False
            print("sinit recibido")
            continue

        try:
            contenido = data.decode()[5:]
            partes = contenido.strip().split('|')
            if len(partes) != 2:
                raise ValueError("Formato incorrecto")

            mes, anio = int(partes[0]), int(partes[1])

            cursor.execute("""
                SELECT u.rut, u.nombre, u.apellido,
                    COUNT(a.hora_entrada) AS asistencias,
                    COUNT(CASE WHEN a.hora_entrada IS NULL AND a.hora_salida IS NULL THEN 1 END) AS inasistencias,
                    COUNT(j.id_justificacion) AS justificaciones
                FROM USUARIO u
                LEFT JOIN ASISTENCIAS a ON u.id_usuario = a.id_usuario
                    AND EXTRACT(MONTH FROM a.fecha) = %s
                    AND EXTRACT(YEAR FROM a.fecha) = %s
                LEFT JOIN JUSTIFICACIONES j ON u.id_usuario = j.id_usuario
                    AND EXTRACT(MONTH FROM j.fecha) = %s
                    AND EXTRACT(YEAR FROM j.fecha) = %s
                WHERE u.rol = 'empleado'
                GROUP BY u.rut, u.nombre, u.apellido
            """, (mes, anio, mes, anio))

            filas = cursor.fetchall()
            resumen = []

            for fila in filas:
                resumen.append({
                    "rut": fila[0],
                    "nombre": fila[1],
                    "apellido": fila[2],
                    "asistencias": fila[3],
                    "inasistencias": fila[4],
                    "justificaciones": fila[5]
                })

            respuesta_json = json.dumps(resumen, ensure_ascii=False)
            mensaje = f"RPORT|{respuesta_json}"

        except Exception as e:
            mensaje = f"RPORT|Error: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", mensaje)
        sock.sendall(f"{largo}{mensaje}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
