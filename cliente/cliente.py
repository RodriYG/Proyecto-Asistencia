import socket
import json

def enviar_transaccion(servicio, datos):

    cuerpo = f"{servicio}{datos}"
    mensaje = f"{len(cuerpo):05}{cuerpo}".encode('utf-8')
    print(f"Enviando (con largo): {mensaje.decode('utf-8')}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('localhost', 5000))
        sock.sendall(mensaje)

        header = sock.recv(5)
        if not header:
            raise RuntimeError("No se recibió encabezado del servidor.")
        largo = int(header.decode('utf-8'))

        buffer = b''
        while len(buffer) < largo:
            chunk = sock.recv(largo - len(buffer))
            if not chunk:
                break
            buffer += chunk

        respuesta = buffer.decode('utf-8')
    print(f"Recibido (con largo): {largo:05}{respuesta}")
    return respuesta

def paginar_reporte(mes, anio, page_size=8):

    offset = 0

    while True:
        datos = f"{mes}|{anio}|{offset}"
        respuesta = enviar_transaccion("RPORT", datos)

        partes = respuesta.split("|", 1)
        if len(partes) != 2:
            print("Respuesta malformada:", respuesta)
            return

        status, json_data = partes

        if status == "RPORTNK":
            print("Error desde RPORT:", json_data)
            return

        if not status.startswith("RPORTOK"):
            print("Prefijo inesperado:", status)
            return

        try:
            usuarios = json.loads(json_data)
        except Exception as e:
            print("Error al parsear JSON:", e)
            print("Contenido recibido:", json_data)
            return

        if not usuarios:
            if offset == 0:
                print("No hay empleados en el reporte.")
            else:
                print("— Fin del listado —")
            return

        primera = offset + 1
        ultima = offset + len(usuarios)
        print(f"\nMostrando empleados {primera} a {ultima}:\n")
        print(" RUT        | Nombre     | Apellido    | Asistencias | Inasistencias | Justificaciones")
        print("------------|------------|-------------|-------------|---------------|----------------")
        for u in usuarios:
            print(f" {u['rut']:<10}| {u['nombre']:<10}| {u['apellido']:<11}|"
                  f"     {u['asistencias']:<3}     |       {u['inasistencias']:<3}     |"
                  f"       {u['justificaciones']:<3}")

        if len(usuarios) < page_size:
            print("\n— Fin del listado —")
            return

        seguir = input("\n¿Mostrar siguientes 8? (s/n): ").strip().lower()
        if seguir != 's':
            print("Deteniendo paginado.")
            return

        offset += page_size

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
            print("6. Reporte mensual (paginar de a 8)")
        print("0. Cerrar sesión")

        op = input("Opción: ").strip()
        if op == "0":
            print("Sesión cerrada.")
            break

        if rol.upper() == "EMPLEADO":
            if op == "1":
                tipo = input("¿Qué deseas marcar? (entrada/salida): ").strip().lower()
                if tipo in ["entrada", "salida"]:
                    datos = f"{rut} {tipo}"
                    resp = enviar_transaccion("MASIS", datos)
                    print("Respuesta:", resp)
                else:
                    print("Tipo inválido.")

            elif op == "2":
                fecha = input("Fecha a justificar (YYYY-MM-DD): ").strip()
                motivo = input("Motivo de la inasistencia: ").strip()
                datos = f"{rut}|{fecha}|{motivo}"
                resp = enviar_transaccion("JUSTI", datos)
                print("Respuesta:", resp)

            elif op == "3":
                fecha_inicio = input("Fecha de inicio (YYYY-MM-DD): ").strip()
                fecha_fin = input("Fecha de fin (YYYY-MM-DD): ").strip()
                datos = f"{rut}|{fecha_inicio}|{fecha_fin}"
                resp = enviar_transaccion("HISTO", datos)
                print("Historial:\n", resp)

            elif op == "4":
                resp = enviar_transaccion("VTURN", rut)
                if resp.startswith("VTURNOK"):
                    contenido = resp[6:].strip() 
                    turnos = contenido.split(";;")
                    print("\nTurnos asignados:")
                    for t in turnos:
                        print(f"  • {t.strip()}")
                else:
                    print("Turnos:", resp[6:])

            else:
                print("Funcionalidad aún no implementada para EMPLEADO.")

        else:  
            if op == "1":
                rut_buscar = input("Ingrese el RUT del empleado a buscar: ").strip()
                resp = enviar_transaccion("BUSCA", rut_buscar)
                print("Resultado:\n", resp)

            elif op == "2":
                print("\n--- Asignar Turno a Empleado ---")
                rut_emp = input("RUT del empleado: ").strip()
                f_ini = input("Fecha de inicio del turno (YYYY-MM-DD): ").strip()
                f_fin = input("Fecha de fin del turno (YYYY-MM-DD): ").strip()
                datos = f"{rut_emp}|{f_ini}|{f_fin}"
                resp = enviar_transaccion("TUPER", datos)
                print("Resultado TUPER:\n", resp)

            elif op == "3":
                rut_emp = input("RUT del empleado: ").strip()
                f_ini = input("Fecha de inicio (YYYY-MM-DD): ").strip()
                f_fin = input("Fecha de fin (YYYY-MM-DD): ").strip()
                datos = f"{rut_emp}|{f_ini}|{f_fin}"
                resp = enviar_transaccion("HISTO", datos)
                print("Historial del empleado:\n", resp)

            elif op == "4":
                rut_emp = input("RUT del empleado a modificar: ").strip()
                fecha = input("Fecha (YYYY-MM-DD): ").strip()
                nueva_hora = input("Nueva hora de entrada (HH:MM): ").strip()
                motivo = input("Motivo de la modificación: ").strip()
                autorizado = rut
                datos = f"{rut_emp}|{fecha}|{nueva_hora}|{motivo}|{autorizado}"
                resp = enviar_transaccion("MODAS", datos)
                print("Resultado modificación:\n", resp)

            elif op == "5":
                sub = input("¿Registrar (r) o eliminar (e) un trabajador?: ").strip().lower()
                if sub == "r":
                    print("Ingrese datos del nuevo trabajador:")
                    rut_nuevo = input("RUT: ").strip()
                    nom = input("Nombre: ").strip()
                    ape = input("Apellido: ").strip()
                    email = input("Correo: ").strip()
                    pw = input("Contraseña: ").strip()
                    rol_nuevo = input("Rol (empleado/empleador): ").strip().lower()
                    datos = f"{rut_nuevo}|{nom}|{ape}|{email}|{pw}|{rol_nuevo}"
                    resp = enviar_transaccion("REGEL", datos)
                    print("Resultado registro:\n", resp)

                elif sub == "e":
                    rut_elim = input("RUT a eliminar: ").strip()
                    resp = enviar_transaccion("REGEL", rut_elim)
                    print("Resultado eliminación:\n", resp)

                else:
                    print("Opción inválida.")
                    continue

            elif op == "6":
                mes = input("Mes (1-12): ").strip()
                anio = input("Año (YYYY): ").strip()
                paginar_reporte(mes, anio, page_size=8)

            else:
                print("Funcionalidad aún no implementada para EMPLEADOR.")

def main():
    while True:
        if input('¿Enviar login? (y/n): ').strip().lower() != 'y':
            break

        datos = input("Correo y contraseña: ").strip()
        resp = enviar_transaccion("LOGIN", datos)

        if resp.startswith("LOGIN"):
            try:
                partes = resp[5:].strip().split(maxsplit=3)
                token = partes[0]
                rol = partes[1]
                msg = partes[2]
                rut = partes[3]
                print(f"Login exitoso: Rol {rol}, Bienvenida: {msg}")
                mostrar_menu_rol(rol, rut)
            except Exception as e:
                print("Error al interpretar respuesta LOGIN:", e)
        else:
            print("Error de login:", resp)

if __name__ == "__main__":
    main()
