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
print("Conectando al bus:", bus_address)
sock.connect(bus_address)

sinit = b'00010sinitHISTO'
print("Enviando sinit:", sinit)
sock.sendall(sinit)
esperando_sinit = True

try:
    while True:
        print("Esperando transacción HISTO...")
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
            if len(partes) != 3:
                raise ValueError("Formato incorrecto. Se esperaban 3 partes.")

            rut, fecha_inicio_str, fecha_fin_str = partes
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            usuario = cursor.fetchone()

            if not usuario:
                mensaje = "HISTONKUsuario no encontrado"
            else:
                id_usuario = usuario[0]

                cursor.execute("""
                    SELECT fecha, hora_entrada, hora_salida
                    FROM ASISTENCIAS
                    WHERE id_usuario = %s AND fecha BETWEEN %s AND %s
                    ORDER BY fecha ASC
                """, (id_usuario, fecha_inicio, fecha_fin))

                registros = cursor.fetchall()
                if not registros:
                    mensaje = "HISTOOKSin registros en el rango indicado"
                else:
                    mensaje = "HISTOOKHistorial de asistencias:\n"
                    for fecha, entrada, salida in registros:
                        entrada_str = entrada.strftime('%H:%M:%S') if entrada else "N/A"
                        salida_str = salida.strftime('%H:%M:%S') if salida else "N/A"
                        mensaje += f"{fecha} - Entrada: {entrada_str}, Salida: {salida_str}\n"

        except Exception as e:
            mensaje = f"HISTONKError: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", mensaje)
        sock.sendall(f"{largo}{mensaje}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
