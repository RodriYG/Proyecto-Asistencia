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
            contenido = datos.decode().strip()
            print("Contenido recibido:", contenido)

            if not contenido.startswith("JUSTI"):
                raise ValueError("Prefijo inválido. Se esperaba 'JUSTI'.")

            contenido = contenido[5:].strip()
            partes = contenido.split('|')

            if len(partes) != 3:
                raise ValueError("Formato incorrecto. Se esperaban: rut|fecha|motivo.")

            rut_str, fecha_str, motivo = [p.strip() for p in partes]

            if not rut_str or not fecha_str or not motivo:
                raise ValueError("Ningún campo puede estar vacío.")

            if not rut_str.isdigit():
                raise ValueError("El RUT debe contener solo números.")

            rut = int(rut_str)

            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("La fecha debe tener formato YYYY-MM-DD.")

            if fecha > datetime.now().date():
                raise ValueError("No se puede justificar una inasistencia en una fecha futura.")

            fecha_solicitud = datetime.now()

            # Verificar existencia del usuario
            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            user = cursor.fetchone()

            if not user:
                raise ValueError("Usuario no encontrado.")

            id_usuario = user[0]

            # Verificar si ya existe una justificación para esa fecha
            cursor.execute("""
                SELECT 1 FROM JUSTIFICACIONES
                WHERE id_usuario = %s AND fecha = %s
            """, (id_usuario, fecha))

            if cursor.fetchone():
                raise ValueError("Ya existe una justificación registrada para esa fecha.")

            # Insertar justificación
            cursor.execute("""
                INSERT INTO JUSTIFICACIONES (id_usuario, fecha, motivo, estado, fecha_solicitud)
                VALUES (%s, %s, %s, 'pendiente', %s)
            """, (id_usuario, fecha, motivo, fecha_solicitud))
            conn.commit()
            respuesta = "JUSTIOKJustificación registrada como pendiente"

        except Exception as e:
            conn.rollback()
            print("Error:", e)
            respuesta = f"JUSTINKError: {str(e)}"

        mensaje_respuesta = f"{len(respuesta):05}{respuesta}"
        print("Enviando respuesta:", mensaje_respuesta)
        sock.sendall(mensaje_respuesta.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
