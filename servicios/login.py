import socket
import psycopg2

# Conexión a PostgreSQL (Docker externo)
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
print('Conectando a {}:{}'.format(*bus_address))
sock.connect(bus_address)

sinit = b'00010sinitLOGIN'
print('Enviando sinit:', sinit)
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

        entrada = data.decode().strip()
        print(f"Datos recibidos: {entrada}")

        try:
            if not entrada.startswith("LOGIN"):
                raise ValueError("Prefijo inválido. Se esperaba LOGIN.")

            entrada = entrada[5:].strip()

            if not entrada:
                raise ValueError("Debe ingresar correo y contraseña.")

            partes = entrada.split()
            if len(partes) != 2:
                raise ValueError("Formato incorrecto. Use: correo contraseña")

            email, password = partes
            email = email.lower()  # Normaliza el email (opcional)

            cursor.execute(
                "SELECT rol, rut FROM USUARIO WHERE email = %s AND password = %s",
                (email, password)
            )
            resultado_query = cursor.fetchone()

            if resultado_query:
                rol, rut = resultado_query
                token = "token123"
                resultado = f"{token} {rol.upper()} Bienvenido {rut}"
                estado = "OK"
            else:
                resultado = "Credenciales inválidas"
                estado = "NK"

        except Exception as e:
            resultado = f"Error: {e}"
            estado = "NK"

        mensaje_respuesta = f"LOGIN{estado}{resultado}"
        largo_respuesta = f"{len(mensaje_respuesta):05}"
        respuesta_final = f"{largo_respuesta}{mensaje_respuesta}"

        print("Enviando respuesta:", respuesta_final)
        sock.sendall(respuesta_final.encode())

finally:
    print("Cerrando conexiones")
    cursor.close()
    conn.close()
    sock.close()
