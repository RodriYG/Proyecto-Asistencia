import socket
import psycopg2
from datetime import datetime, date

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

sinit = b'00010sinitMASIS'
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
            partes = contenido.strip().split()
            if len(partes) != 2:
                raise ValueError("Formato incorrecto")

            rut, tipo = partes
            hoy = date.today()

            cursor.execute("SELECT id_usuario FROM USUARIO WHERE rut = %s", (rut,))
            user = cursor.fetchone()

            if not user:
                mensaje = "MASIS Usuario no encontrado NK -"
            else:
                id_usuario = user[0]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if tipo == "entrada":
                    cursor.execute("""
                        SELECT * FROM ASISTENCIAS
                        WHERE id_usuario = %s AND fecha = %s
                    """, (id_usuario, hoy))
                    existe = cursor.fetchone()

                    if existe:
                        mensaje = f"MASISEntrada ya registrada NK {timestamp}"
                    else:
                        cursor.execute("""
                            INSERT INTO ASISTENCIAS (id_usuario, fecha, hora_entrada)
                            VALUES (%s, %s, %s)
                        """, (id_usuario, hoy, datetime.now().time()))
                        conn.commit()
                        mensaje = f"MASIS Entrada registrada OK {timestamp}"

                elif tipo == "salida":
                    cursor.execute("""
                        SELECT * FROM ASISTENCIAS
                        WHERE id_usuario = %s AND fecha = %s AND hora_salida IS NULL
                    """, (id_usuario, hoy))
                    fila = cursor.fetchone()

                    if fila:
                        cursor.execute("""
                            UPDATE ASISTENCIAS
                            SET hora_salida = %s
                            WHERE id_usuario = %s AND fecha = %s
                        """, (datetime.now().time(), id_usuario, hoy))
                        conn.commit()
                        mensaje = f"MASISSalida registrada OK {timestamp}"
                    else:
                        mensaje = f"MASISNo se encontró entrada previa NK {timestamp}"
                else:
                    mensaje = f"MASISTipo inválido NK {timestamp}"

        except Exception as e:
            conn.rollback() 
            mensaje = f"MASISError: {str(e)} NK -"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", mensaje)
        sock.sendall(f"{largo}{mensaje}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
