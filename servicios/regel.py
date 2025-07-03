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

        contenido = datos.decode().strip()
        print("Contenido recibido:", contenido)

        try:
            contenido = contenido[5:].strip()  # eliminar prefijo REGEL si existe
            partes = contenido.split('|')

            if len(partes) == 1:
                # Eliminar trabajador
                rut = partes[0].strip()

                if not rut:
                    raise ValueError("Debe proporcionar un RUT.")

                cursor.execute("SELECT 1 FROM USUARIO WHERE rut = %s", (rut,))
                if not cursor.fetchone():
                    raise ValueError("No se encontró ningún trabajador con ese RUT.")

                cursor.execute("DELETE FROM USUARIO WHERE rut = %s", (rut,))
                conn.commit()
                mensaje = "REGELOK|Trabajador eliminado correctamente"

            elif len(partes) == 6:
                # Registrar trabajador
                rut, nombre, apellido, email, password, rol = [p.strip() for p in partes]

                if any(not campo for campo in [rut, nombre, apellido, email, password, rol]):
                    raise ValueError("Todos los campos deben estar completos.")

                if rol.lower() not in ["empleado", "empleador"]:
                    raise ValueError("El rol debe ser 'empleado' o 'empleador'.")

                # Verificar que no exista duplicado
                cursor.execute("SELECT 1 FROM USUARIO WHERE rut = %s OR email = %s", (rut, email))
                if cursor.fetchone():
                    raise ValueError("Ya existe un trabajador con ese RUT o correo.")

                cursor.execute("""
                    INSERT INTO USUARIO (rut, nombre, apellido, email, password, rol)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (rut, nombre, apellido, email, password, rol.lower()))
                conn.commit()
                mensaje = "REGELOK|Trabajador registrado correctamente"

            else:
                raise ValueError("Formato inválido. Se esperaban 1 o 6 campos.")

        except Exception as e:
            conn.rollback()
            mensaje = f"REGELNK|Error: {str(e)}"

        largo = f"{len(mensaje):05}"
        print("Enviando respuesta:", largo + mensaje)
        sock.sendall((largo + mensaje).encode())

finally:
    cursor.close()
    conn.close()
    sock.close()
