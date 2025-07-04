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

        # Leer todo el cuerpo
        data = b""
        while len(data) < largo:
            data += sock.recv(largo - len(data))

        print("Recibido:", data)

        if esperando_sinit:
            esperando_sinit = False
            print("sinit recibido")
            continue

        try:
            contenido = data.decode().strip()
            if not contenido.startswith("HISTO"):
                raise ValueError("Prefijo inválido. Se esperaba 'HISTO'.")

            contenido = contenido[5:].strip()
            partes = contenido.split('|')

            if len(partes) != 4:
                raise ValueError("Formato incorrecto. Se esperaban: rut|fecha_inicio|fecha_fin|offset.")

            rut, fecha_inicio_str, fecha_fin_str, offset_str = [p.strip() for p in partes]

            if not rut.isdigit() or not (7 <= len(rut) <= 9):
                raise ValueError("El RUT debe contener solo números y tener entre 7 y 9 dígitos.")

            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD.")

            if fecha_fin < fecha_inicio:
                raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")

            if not offset_str.isdigit():
                raise ValueError("El offset debe ser un número entero.")
            offset = int(offset_str)

            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            usuario = cursor.fetchone()

            if not usuario:
                respuesta = "HISTONKUsuario no encontrado"
            else:
                id_usuario = usuario[0]

                cursor.execute("""
                    SELECT fecha, hora_entrada, hora_salida
                    FROM ASISTENCIAS
                    WHERE id_usuario = %s AND fecha BETWEEN %s AND %s
                    ORDER BY fecha ASC
                    LIMIT 10 OFFSET %s
                """, (id_usuario, fecha_inicio, fecha_fin, offset))

                registros = cursor.fetchall()

                if not registros:
                    if offset == 0:
                        respuesta = "HISTOOKNo hay registros en ese rango de fechas."
                    else:
                        respuesta = "HISTOOK— Fin del historial —"
                else:
                    lineas = []
                    for fecha, entrada, salida in registros:
                        entrada_str = entrada.strftime('%H:%M:%S') if entrada else "N/A"
                        salida_str = salida.strftime('%H:%M:%S') if salida else "N/A"
                        lineas.append(f"{fecha} - Entrada: {entrada_str}, Salida: {salida_str}")
                    
                    historial = "\n".join(lineas)
                    respuesta = f"HISTOOK{historial}"

        except Exception as e:
            conn.rollback()
            print("Error:", e)
            respuesta = f"HISTONKError: {str(e)}"

        largo = f"{len(respuesta):05}"
        print("Enviando respuesta:", respuesta)
        sock.sendall(f"{largo}{respuesta}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
