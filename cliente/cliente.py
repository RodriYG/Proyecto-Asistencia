import socket

def enviar_transaccion(servicio, datos):
    cuerpo = f"{servicio}{datos}"
    mensaje = f"{len(cuerpo):05}{cuerpo}"
    print(f"📤 Enviando (con largo): {mensaje}")  # Muestra mensaje completo
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('localhost', 5000))
        sock.sendall(mensaje.encode())
        largo = int(sock.recv(5))
        respuesta = sock.recv(largo).decode()
    print(f"Recibido (con largo): {largo:05}{respuesta}")
    return respuesta


def mostrar_menu_rol(rol, rut):
    while True:
        print(f"\n--- Menú de {rol.upper()} ---")
        if rol.upper() == "EMPLEADO":
            print("1. Marcar asistencia")
            print("2. Justificar inasistencia")
            print("3. Ver historial")
        elif rol.upper() == "EMPLEADOR":
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

        elif rol.upper() == "EMPLEADO" and op == "1":
            tipo = input("¿Qué deseas marcar? (entrada/salida): ").strip().lower()
            if tipo in ["entrada", "salida"]:
                datos = f"{rut} {tipo}"
                respuesta = enviar_transaccion("MASIS", datos)
                print("Respuesta:", respuesta)
            else:
                print("Tipo inválido.")

        elif rol.upper() == "EMPLEADO" and op == "2":
            fecha = input("Fecha a justificar (YYYY-MM-DD): ")
            motivo = input("Motivo de la inasistencia: ")
            datos = f"{rut}|{fecha}|{motivo}"
            respuesta = enviar_transaccion("JASIS", datos)
            print("Respuesta:", respuesta)

        elif rol.upper() == "EMPLEADO" and op == "3":
            fecha_inicio = input("Fecha de inicio (YYYY-MM-DD): ").strip()
            fecha_fin = input("Fecha de fin (YYYY-MM-DD): ").strip()
            datos = f"{rut}|{fecha_inicio}|{fecha_fin}"
            respuesta = enviar_transaccion("HISTO", datos)
            print("Historial:\n", respuesta)

        elif rol.upper() == "EMPLEADOR" and op == "1":
            rut_buscar = input("Ingrese el RUT del empleado a buscar: ")
            respuesta = enviar_transaccion("BUSCA", rut_buscar)
            print("Resultado:\n", respuesta)

        elif rol.upper() == "EMPLEADOR" and op == "3":
            rut_empleado = input("RUT del empleado: ").strip()
            fecha_inicio = input("Fecha de inicio (YYYY-MM-DD): ").strip()
            fecha_fin = input("Fecha de fin (YYYY-MM-DD): ").strip()
            datos = f"{rut_empleado}|{fecha_inicio}|{fecha_fin}"
            respuesta = enviar_transaccion("HISTO", datos)
            print("Historial del empleado:\n", respuesta)

        elif rol.upper() == "EMPLEADOR" and op == "5":
            subop = input("¿Desea registrar (r) o eliminar (e) un trabajador?: ").strip().lower()
            if subop == "r":
                print("Ingrese los datos del nuevo trabajador:")
                rut_nuevo = input("RUT: ").strip()
                nombre = input("Nombre: ").strip()
                apellido = input("Apellido: ").strip()
                email = input("Correo: ").strip()
                password = input("Contraseña: ").strip()
                rol_nuevo = input("Rol (empleado/empleador): ").strip().lower()
                datos = f"{rut_nuevo}|{nombre}|{apellido}|{email}|{password}|{rol_nuevo}"
                respuesta = enviar_transaccion("REGEL", datos)
                print("Resultado:", respuesta)
            elif subop == "e":
                rut_eliminar = input("RUT del trabajador a eliminar: ").strip()
                respuesta = enviar_transaccion("REGEL", rut_eliminar)
                print("Resultado:", respuesta)
            else:
                print("Opción inválida.")
        
        elif rol.upper() == "EMPLEADOR" and op == "6":
            mes = input("Ingrese el mes (1-12): ").strip()
            anio = input("Ingrese el año (YYYY): ").strip()
            datos = f"{mes}|{anio}"
            respuesta = enviar_transaccion("RPORT", datos)
            print("Reporte mensual:\n", respuesta)


        else:
            print("Funcionalidad aún no implementada.")

def main():
    while True:
        if input('¿Enviar login? (y/n): ') != 'y':
            break

        datos = input("Correo y contraseña: ")  # Ej: pedro@mail.com panchito
        respuesta = enviar_transaccion("LOGIN", datos)

        if respuesta.startswith("LOGIN"):
            try:
                partes = respuesta[5:].strip().split(maxsplit=3)
                token = partes[0]
                rol = partes[1]
                mensaje = partes[2]
                rut = partes[3]
                print(f"Login exitoso: Rol {rol}, Bienvenida: {mensaje}")
                mostrar_menu_rol(rol, rut)
            except Exception as e:
                print("Error al interpretar la respuesta del servidor:", str(e))
        else:
            print("Error de login")

if __name__ == "__main__":
    main()
