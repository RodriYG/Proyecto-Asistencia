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

# Socket servidor
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5000))
print("Conectado al bus")

# Envío sinit
sinit = b'00010sinitMODAS'
print("Enviando sinit:", sinit)
sock.sendall(sinit)
esperando_sinit = True

try:
    while True:
        print("Esperando transacción...")
        largo = int(sock.recv(5))
        datos = sock.recv(largo)
        print("Recibido:", datos)

        if esperando_sinit:
            esperando_sinit = False
            print("sinit recibido")
            continue

        try:
            contenido = datos.decode().strip()
            print("Contenido recibido:", contenido)

            if not contenido.startswith("MODAS"):
                raise ValueError("Prefijo inválido. Se esperaba 'MODAS'.")

            contenido = contenido[5:].strip()
            partes = contenido.split('|')

            if len(partes) != 5:
                raise ValueError("Formato incorrecto. Se esperaban 5 partes: rut|fecha|hora|motivo|autorizado.")

            rut, fecha_str, nueva_hora_str, motivo, autorizado = [p.strip() for p in partes]

            # Validar campos vacíos
            if any(not campo for campo in [rut, fecha_str, nueva_hora_str, motivo, autorizado]):
                raise ValueError("Ningún campo puede estar vacío.")

            # Validar RUTs numéricos
            if not rut.isdigit():
                raise ValueError("El RUT del empleado debe contener solo números.")
            if not autorizado.isdigit():
                raise ValueError("El RUT autorizado debe contener solo números.")

            # Validar fecha
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha debe tener formato YYYY-MM-DD.")

            # Validar hora
            try:
                nueva_hora = datetime.strptime(nueva_hora_str, "%H:%M").time()
            except ValueError:
                raise ValueError("La hora debe tener formato HH:MM.")

            # Validar que el usuario exista
            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("Empleado no encontrado.")
            id_usuario = user[0]

            # Validar que el usuario autorizador exista
            cursor.execute("SELECT 1 FROM USUARIO WHERE rut = %s", (autorizado,))
            if not cursor.fetchone():
                raise ValueError("El RUT autorizado no existe.")

            # Validar que exista una asistencia en esa fecha
            cursor.execute("""
                SELECT id_asistencia, hora_entrada
                FROM ASISTENCIAS
                WHERE id_usuario = %s AND fecha = %s
            """, (id_usuario, fecha))
            asistencia = cursor.fetchone()

            if not asistencia:
                raise ValueError("No existe asistencia en esa fecha.")

            id_asistencia, entrada_anterior = asistencia

            # Realizar modificación
            cursor.execute("""
                UPDATE ASISTENCIAS
                SET hora_entrada = %s
                WHERE id_asistencia = %s
            """, (nueva_hora, id_asistencia))

            conn.commit()
            mensaje = f"MODAS|OK|Entrada modificada: {entrada_anterior} -> {nueva_hora}"

        except Exception as e:
            conn.rollback()
            print("Error:", e)
            mensaje = f"MODAS|NK|Error: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", mensaje)
        sock.sendall(f"{largo}{mensaje}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
