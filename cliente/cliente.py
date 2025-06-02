import socket
import json

def enviar_transaccion(servicio, datos):
    cuerpo = f"{servicio}{datos}"
    mensaje = f"{len(cuerpo):05}{cuerpo}"
    print(f"Enviando (con largo): {mensaje}")
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
            print("4. Ver turnos asignados")
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

        # --- EMPLEADO ---
        if rol.upper() == "EMPLEADO":
            if op == "1":
                tipo = input("¿Qué deseas marcar? (entrada/salida): ").strip().lower()
                if tipo in ["entrada", "salida"]:
                    datos = f"{rut} {tipo}"
                    respuesta = enviar_transaccion("MASIS", datos)
                    print("Respuesta:", respuesta)
                else:
                    print("Tipo inválido.")

            elif op == "2":
                fecha = input("Fecha a justificar (YYYY-MM-DD): ").strip()
                motivo = input("Motivo de la inasistencia: ").strip()
                datos = f"{rut}|{fecha}|{motivo}"
                respuesta = enviar_transaccion("JUSTI", datos)
                print("Respuesta:", respuesta)

            elif op == "3":
                fecha_inicio = input("Fecha de inicio (YYYY-MM-DD): ").strip()
                fecha_fin = input("Fecha de fin (YYYY-MM-DD): ").strip()
                datos = f"{rut}|{fecha_inicio}|{fecha_fin}"
                respuesta = enviar_transaccion("HISTO", datos)
                print("Historial:\n", respuesta)

            elif op == "4":
                respuesta = enviar_transaccion("VTURN", rut)
                if respuesta.startswith("VTURNOK"):
                    contenido = respuesta[5+2:].strip()  
                    turnos = contenido.split(";;")
                    print("\nTurnos asignados:")
                    for t in turnos:
                        print(f"  • {t.strip()}")
                else:
                    print("Turnos:", respuesta[5:])

            else:
                print("Funcionalidad aún no implementada para EMPLEADO.")

        else:
            if op == "1":
                rut_buscar = input("Ingrese el RUT del empleado a buscar: ").strip()
                respuesta = enviar_transaccion("BUSCA", rut_buscar)
                print("Resultado:\n", respuesta)

            elif op == "2":
                print("\n--- Asignar Turno a Empleado ---")
                rut_empleado = input("RUT del empleado: ").strip()
                fecha_inicio = input("Fecha de inicio del turno (YYYY-MM-DD): ").strip()
                fecha_fin = input("Fecha de fin del turno (YYYY-MM-DD): ").strip()
                datos = f"{rut_empleado}|{fecha_inicio}|{fecha_fin}"
                respuesta = enviar_transaccion("TUPER", datos)
                print("Resultado TUPER:\n", respuesta)

            elif op == "3":
                rut_empleado = input("RUT del empleado: ").strip()
                fecha_inicio = input("Fecha de inicio (YYYY-MM-DD): ").strip()
                fecha_fin = input("Fecha de fin (YYYY-MM-DD): ").strip()
                datos = f"{rut_empleado}|{fecha_inicio}|{fecha_fin}"
                respuesta = enviar_transaccion("HISTO", datos)
                print("Historial del empleado:\n", respuesta)

            elif op == "4":
                rut_empleado = input("RUT del empleado a modificar: ").strip()
                fecha = input("Fecha (YYYY-MM-DD): ").strip()
                nueva_hora = input("Nueva hora de entrada (HH:MM): ").strip()
                motivo = input("Motivo de la modificación: ").strip()
                autorizado = rut
                datos = f"{rut_empleado}|{fecha}|{nueva_hora}|{motivo}|{autorizado}"
                respuesta = enviar_transaccion("MODAS", datos)
                print("Resultado modificación:\n", respuesta)

            elif op == "5":
                subop = input("¿Desea registrar (r) o eliminar (e) un trabajador?: ").strip().lower()
                if subop == "r":
                    print("Ingrese datos del nuevo trabajador:")
                    rut_nuevo = input("RUT: ").strip()
                    nombre = input("Nombre: ").strip()
                    apellido = input("Apellido: ").strip()
                    email = input("Correo: ").strip()
                    password = input("Contraseña: ").strip()
                    rol_nuevo = input("Rol (empleado/empleador): ").strip().lower()
                    datos = f"{rut_nuevo}|{nombre}|{apellido}|{email}|{password}|{rol_nuevo}"
                    respuesta = enviar_transaccion("REGEL", datos)
                    print("Resultado registro:\n", respuesta)
                elif subop == "e":
                    rut_eliminar = input("RUT trabajador a eliminar: ").strip()
                    respuesta = enviar_transaccion("REGEL", rut_eliminar)
                    print("Resultado eliminación:\n", respuesta)
                else:
                    print("Opción inválida.")

            elif op == "6":
                mes = input("Mes (1-12): ").strip()
                anio = input("Año (YYYY): ").strip()
                datos = f"{mes}|{anio}"
                respuesta = enviar_transaccion("RPORT", datos)
            
                try:
                    status, json_data = respuesta.split("|", 1)
                    if status != "RPORTOK":
                        print("Error en la respuesta:", respuesta)
                    else:
                        reporte = json.loads(json_data)
            
                        # Imprimir tabla
                        print("\nReporte mensual:\n")
                        print("RUT        | Nombre    | Apellido   | Asistencias | Inasistencias | Justificaciones")
                        print("-----------|-----------|------------|-------------|---------------|----------------")
                        for persona in reporte:
                            print(f"{persona['rut']:<11}| {persona['nombre']:<10}| {persona['apellido']:<11}|"
                                  f"     {persona['asistencias']:<3}     |       {persona['inasistencias']:<3}     |"
                                  f"       {persona['justificaciones']:<3}")
                except Exception as e:
                    print("Error procesando el reporte:", e)
                    print("Respuesta recibida:", respuesta)


            else:
                print("Funcionalidad aún no implementada para EMPLEADOR.")

def main():
    while True:
        if input('¿Enviar login? (y/n): ') != 'y':
            break

        datos = input("Correo y contraseña: ").strip()
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
