import socket
import psycopg2

# Conexión a la base de datos
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="asistencia",
    user="user",
    password="user"
)
cursor = conn.cursor()

# Conexión al bus
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5000))
sock.sendall(b'00010sinitREGEL')
sinit = True

try:
    while True:
        print("Esperando transacción REGEL...")
        largo = int(sock.recv(5))
        datos = sock.recv(largo)
        print("Recibido:", datos)

        if sinit:
            sinit = False
            print("Sinit REGEL recibido.")
            continue

        contenido = datos.decode()[5:].strip()
        partes = contenido.split('|')

        try:
            if len(partes) == 1:
                rut = partes[0]
                cursor.execute("DELETE FROM USUARIO WHERE rut = %s", (rut,))
                conn.commit()
                mensaje = "REGELOK|Trabajador eliminado correctamente"

            elif len(partes) == 6:
                rut, nombre, apellido, email, password, rol = partes
                cursor.execute("""
                    INSERT INTO USUARIO (rut, nombre, apellido, email, password, rol)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (rut, nombre, apellido, email, password, rol))
                conn.commit()
                mensaje = "REGELOK|Trabajador registrado correctamente"

            else:
                mensaje = "REGELNK|Formato inválido"

        except Exception as e:
            mensaje = f"REGELNK|Error: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", largo + mensaje)
        sock.sendall((largo + mensaje).encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
