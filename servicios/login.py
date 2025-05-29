import socket
import psycopg2

# Conexión al PostgreSQL del contenedor Docker
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
print('connecting to {} port {}'.format(*bus_address))
sock.connect(bus_address)

message = b'00010sinitLOGIN'
print('sending {!r}'.format(message))
sock.sendall(message)
sinit = 1

try:
    while True:
        print("Waiting for transaction")
        amount_expected = int(sock.recv(5))
        data = sock.recv(amount_expected)
        print("Processing...")
        print('received {!r}'.format(data))

        if sinit == 1:
            sinit = 0
            print('Received sinit answer')
        else:
            entrada = data.decode()[5:]  # quitar 'LOGIN'
            print(f'Datos recibidos: {entrada}')

            try:
                email, password = entrada.strip().split()

                cursor.execute(
                    "SELECT rol FROM USUARIO WHERE email = %s AND password = %s",
                    (email, password)
                )
                resultado_query = cursor.fetchone()

                if resultado_query:
                    rol = resultado_query[0].upper()  # lo convertimos a mayúsculas por consistencia
                    token = "token123"
                    resultado = f"{token} {rol} Bienvenido {email}"
                    estado = "OK"
                else:
                    resultado = "Credenciales inválidas"
                    estado = "NK"

            except Exception as e:
                resultado = f"Error: {e}"
                estado = "NK"

            mensaje_respuesta = f"LOGIN{estado}{resultado}"
            largo = f"{len(mensaje_respuesta):05}"
            respuesta = f"{largo}{mensaje_respuesta}"
            print(f'sending {respuesta}')
            sock.sendall(respuesta.encode())

finally:
    print('closing socket')
    cursor.close()
    conn.close()
    sock.close()
