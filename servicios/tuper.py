import socket
import psycopg2
from datetime import datetime

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

sinit = b'00010sinitTUPER'
print("Enviando sinit:", sinit)
sock.sendall(sinit)
esperando_sinit = True

try:
    while True:
        print("Esperando transacción TUPER...")
        largo = int(sock.recv(5))
        data = sock.recv(largo)
        print("Recibido:", data)

        if esperando_sinit:
            esperando_sinit = False
            print("sinit recibido")
            continue

        contenido = data.decode()[5:].strip()
        partes = contenido.split('|')

        try:
            if len(partes) != 3:
                raise ValueError("Formato incorrecto. Deben ser 3 campos (rut|fecha_inicio|fecha_fin).")

            rut = partes[0].strip()
            fecha_inicio_str = partes[1].strip()
            fecha_fin_str = partes[2].strip()

            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Empleado no encontrado.")

            id_usuario = user[0]

            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            if fecha_fin < fecha_inicio:
                raise ValueError("La fecha de fin no puede ser anterior a la fecha de inicio.")

            id_turno = 1

            cursor.execute("""
                INSERT INTO TURNOS_ASIGNADOS (id_usuario, id_turno, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s)
            """, (id_usuario, id_turno, fecha_inicio, fecha_fin))
            conn.commit()

            mensaje = "TUPER|OK|Turno asignado correctamente"

        except Exception as e:
            conn.rollback()
            mensaje = f"TUPER|NK|Error: {str(e)}"

        largo_respuesta = f"{len(mensaje):05}"
        print("Enviando respuesta:", largo_respuesta + mensaje)
        sock.sendall((largo_respuesta + mensaje).encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
