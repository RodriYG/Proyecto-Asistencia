import socket

def enviar_transaccion(servicio, datos):
    cuerpo = f"{servicio}{datos}"
    mensaje = f"{len(cuerpo):05}{cuerpo}"
    print(f"Enviando: {mensaje}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('localhost', 5000))
        sock.sendall(mensaje.encode())
        largo = int(sock.recv(5))
        respuesta = sock.recv(largo).decode()
    return respuesta

def mostrar_menu_rol(rol, correo):
    while True:
        print(f"\n--- Menú de {rol} ---")
        if rol == "EMPLEADO":
            print("1. Marcar asistencia")
            print("2. Justificar inasistencia")
            print("3. Ver historial")
        elif rol == "EMPLEADOR":
            print("1. Buscar empleado")
            print("2. Gestionar turnos y permisos")
            print("3. Ver historial")
            print("4. Modificar asistencia")
            print("5. Registrar/eliminar trabajador")
            print("6. Reporte mensual")
        print("0. Cerrar sesión")
        op = input("Opción: ")
        if op == "0":
            print("Sesión cerrada.")
            break
        elif rol == "EMPLEADO" and op == "1":
            respuesta = enviar_transaccion("MASIS", correo)
            print("🟢 Respuesta del servidor:", respuesta)
        elif rol == "EMPLEADO" and op == "2":
            fecha = input("Fecha a justificar (YYYY-MM-DD): ")
            motivo = input("Motivo de la inasistencia: ")
            datos = f"{correo}|{fecha}|{motivo}"
            respuesta = enviar_transaccion("JUSTI", datos)
            print("🟢 Respuesta del servidor:", respuesta)
        else:
            print("⚠️ Funcionalidad aún no implementada.")


def main():
    while True:
        if input('¿Enviar login? (y/n): ') != 'y':
            break

        datos = input("Correo y contraseña: ") 
        respuesta = enviar_transaccion("LOGIN", datos)
        print(f"Respuesta cruda: {respuesta}")

        if "LOGINOK" in respuesta:
            partes = respuesta.split("LOGINOK")[1].strip().split()
            token = partes[0]
            rol = partes[1]
            correo = partes[3] if len(partes) > 3 else datos.split()[0]
            print(f"Login correcto. Token: {token}, Rol: {rol}, Correo: {correo}")
            mostrar_menu_rol(rol, correo)
        elif "LOGINNK" in respuesta:
            print("Login inválido:", respuesta.split("LOGINNK")[1].strip())
        else:
            print("Respuesta desconocida")

if __name__ == "__main__":
    main()