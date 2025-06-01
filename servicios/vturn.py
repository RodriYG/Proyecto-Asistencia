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
print("Conectando a bus VTURN:", bus_address)
sock.connect(bus_address)

sinit = b'00010sinitVTURN'
sock.sendall(sinit)
esperando_sinit = True

try:
    while True:
        largo = int(sock.recv(5))
        data = sock.recv(largo)

        if esperando_sinit:
            esperando_sinit = False
            continue

        rut = data.decode()[5:].strip()

        try:
            cursor.execute("""
                SELECT 
                  ta.id_turno,
                  COALESCE(t.nombre_turno, '')         AS nombre_turno,
                  t.hora_inicio,
                  t.hora_fin,
                  ta.fecha_inicio,
                  ta.fecha_fin
                FROM TURNOS_ASIGNADOS ta
                LEFT JOIN TURNOS t ON ta.id_turno = t.id_turno
                JOIN USUARIO u   ON ta.id_usuario = u.id_usuario
                WHERE u.rut = %s
                ORDER BY ta.fecha_inicio;
            """, (rut,))

            filas = cursor.fetchall()
            if not filas:
                mensaje = "VTURNNKNo hay turnos asignados"
            else:
                lineas = []
                for id_turno, nombre_turno, hora_i, hora_f, fi, ff in filas:
                    if nombre_turno:
                        desc = f"{nombre_turno}"
                    else:
                        desc = f"TurnoID {id_turno}"

                    hi = hora_i.strftime('%H:%M') if hora_i else "N/A"
                    hf = hora_f.strftime('%H:%M') if hora_f else "N/A"
                    fi_str = fi.strftime('%Y-%m-%d')
                    ff_str = ff.strftime('%Y-%m-%d')
                    lineas.append(f"{fi_str} a {ff_str} → {desc} ({hi}-{hf})")

                contenido = " ;; ".join(lineas)
                mensaje = f"VTURNOK{contenido}"

        except Exception as e:
            mensaje = f"VTURNNKError: {str(e)}"

        salida = f"{len(mensaje):05}{mensaje}"
        print("Enviando respuesta VTURN:", salida)
        sock.sendall(salida.encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
