import socket
import psycopg2
from datetime import datetime, time

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
            contenido = datos.decode()[5:]
            partes = contenido.strip().split('|')

            if len(partes) != 5:
                raise ValueError("Formato incorrecto. Se esperaban 5 partes.")

            rut = partes[0].strip()
            fecha_str = partes[1].strip()  
            nueva_hora_str = partes[2].strip()
            motivo = partes[3].strip()
            autorizado = partes[4].strip()

            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            nueva_hora = datetime.strptime(nueva_hora_str, "%H:%M").time()

            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            user = cursor.fetchone()

            if not user:
                mensaje = "MODAS|NK|Empleado no encontrado"
            else:
                id_usuario = user[0]

                cursor.execute("""
                    SELECT id_asistencia, hora_entrada, hora_salida
                    FROM ASISTENCIAS
                    WHERE id_usuario = %s AND fecha = %s
                """, (id_usuario, fecha))
                asistencia = cursor.fetchone()

                if not asistencia:
                    mensaje = "MODAS|NK|No existe asistencia en esa fecha"
                else:
                    id_asistencia, entrada, salida = asistencia
                    cursor.execute("""
                        UPDATE ASISTENCIAS
                        SET hora_entrada = %s
                        WHERE id_asistencia = %s
                    """, (nueva_hora, id_asistencia))

                    conn.commit()
                    mensaje = f"MODAS|OK|Entrada modificada: {entrada} -> {nueva_hora}"

        except Exception as e:
            mensaje = f"MODAS|NK|Error: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", mensaje)
        sock.sendall(f"{largo}{mensaje}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
