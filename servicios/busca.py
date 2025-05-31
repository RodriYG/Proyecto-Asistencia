import socket
import psycopg2

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

sinit = b'00010sinitBUSCA'
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

        rut = data.decode()[5:].strip()
        print("Buscando RUT:", rut)

        try:
            cursor.execute("""
                SELECT nombre, apellido, email, rol FROM USUARIO WHERE rut = %s
            """, (rut,))
            user = cursor.fetchone()

            if user:
                nombre, apellido, email, rol = user
                mensaje = f"BUSCAOKNombre: {nombre} {apellido}, Email: {email}, Rol: {rol}"
            else:
                mensaje = "BUSCANKNo se encontró un empleado con ese RUT"

        except Exception as e:
            mensaje = f"BUSCANKError: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", mensaje)
        sock.sendall(f"{largo}{mensaje}".encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
