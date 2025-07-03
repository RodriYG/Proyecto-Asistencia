import socket
import psycopg2
import re

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

def rut_valido(rut):
    return bool(re.fullmatch(r"\d{7,9}", rut))  # solo números, largo razonable

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
            rut = data.decode()[5:].strip()
            print("Buscando RUT:", rut)

            if not rut:
                raise ValueError("El RUT está vacío")

            if not rut_valido(rut):
                raise ValueError("Formato de RUT inválido (debe contener solo números y tener entre 7 y 9 dígitos)")

            cursor.execute("""
                SELECT nombre, apellido, email, rol FROM USUARIO WHERE rut = %s
            """, (rut,))
            users = cursor.fetchall()

            if len(users) == 1:
                nombre, apellido, email, rol = users[0]
                mensaje = f"BUSCAOKNombre: {nombre} {apellido}, Email: {email}, Rol: {rol}"
            elif len(users) > 1:
                mensaje = "BUSCANKError: Hay múltiples usuarios con ese RUT (inconsistencia en base de datos)"
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
