import json
import psycopg2
from datetime import datetime
import socket

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
print("Conectando a bus RPORT en {}:{}".format(*bus_address))
sock.connect(bus_address)

sinit = b'00010sinitRPORT'
print("Enviando sinit:", sinit)
sock.sendall(sinit)
esperando_sinit = True

def _leer_encabezado(sock):
    buf = b''
    while True:
        byte = sock.recv(1)
        if not byte:
            raise RuntimeError("Conexión cerrada inesperadamente al leer encabezado")
        buf += byte
        if len(buf) < 5:
            continue
        candidate = buf[-5:]
        try:
            text = candidate.decode('ascii')
        except UnicodeDecodeError:
            buf = buf[1:]
            continue
        if text.isdigit():
            return text
        buf = buf[1:]

while True:
    try:
        header = _leer_encabezado(sock)
        largo = int(header)

        buffer = b''
        while len(buffer) < largo:
            chunk = sock.recv(largo - len(buffer))
            if not chunk:
                raise RuntimeError("Conexión cerrada inesperadamente al leer cuerpo")
            buffer += chunk

        data = buffer
        print("Recibido bytes RPORT:", data[:30], "...(+{} bytes)".format(len(data)))

        if esperando_sinit:
            esperando_sinit = False
            continue

        texto = data.decode('utf-8', errors='ignore')
        if not texto.startswith("RPORT"):
            print("Fragmento no reconocido como RPORT; descartado.")
            continue

        cuerpo_tx = texto[5:]  
        partes = cuerpo_tx.strip().split('|')
        if len(partes) != 3:
            raise ValueError('Formato incorrecto: se esperaban "mes|anio|offset"')

        mes, anio, offset = int(partes[0]), int(partes[1]), int(partes[2])

        cursor.execute("""
            SELECT u.rut, u.nombre, u.apellido,
                   COUNT(a.hora_entrada) AS asistencias,
                   COUNT(
                     CASE 
                       WHEN a.hora_entrada IS NULL AND a.hora_salida IS NULL 
                       THEN 1 
                     END
                   ) AS inasistencias,
                   COUNT(j.id_justificacion) AS justificaciones
              FROM USUARIO u
              LEFT JOIN ASISTENCIAS a 
                ON u.id_usuario = a.id_usuario
               AND EXTRACT(MONTH FROM a.fecha) = %s
               AND EXTRACT(YEAR  FROM a.fecha) = %s
              LEFT JOIN JUSTIFICACIONES j 
                ON u.id_usuario = j.id_usuario
               AND EXTRACT(MONTH FROM j.fecha) = %s
               AND EXTRACT(YEAR  FROM j.fecha) = %s
             WHERE u.rol = 'empleado'
             GROUP BY u.rut, u.nombre, u.apellido
             ORDER BY u.rut
             LIMIT 8 OFFSET %s;
        """, (mes, anio, mes, anio, offset))

        filas = cursor.fetchall()
        resumen = []
        for rut_, nombre, apellido, asist, inas, justi in filas:
            resumen.append({
                "rut": rut_,
                "nombre": nombre,
                "apellido": apellido,
                "asistencias": asist,
                "inasistencias": inas,
                "justificaciones": justi
            })

        respuesta_json = json.dumps(resumen, ensure_ascii=False)

        mensaje = f"RPORT|{respuesta_json}"
        salida_bytes = mensaje.encode('utf-8')
        header_out = f"{len(salida_bytes):05}".encode('utf-8')
        print("Enviando respuesta RPORT:", header_out + salida_bytes)
        sock.sendall(header_out + salida_bytes)

    except Exception as e:
        err_mensaje = f"RPORTNK|Error: {str(e)}"
        salida_err = err_mensaje.encode('utf-8')
        header_err = f"{len(salida_err):05}".encode('utf-8')
        print("Enviando error RPORT:", header_err + salida_err)
        sock.sendall(header_err + salida_err)

cursor.close()
conn.close()
sock.close()
