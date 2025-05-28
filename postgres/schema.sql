CREATE TYPE rol AS ENUM ('empleado', 'empleador');

CREATE TABLE IF NOT EXISTS USUARIO (
    id_usuario serial,
    rut int,
    nombre varchar,
    apellido varchar,
    email varchar,
    password varchar,
    rol rol
);

CREATE TABLE IF NOT EXISTS ASISTENCIAS (
    id_asistencia serial,
    id_usuario int,
    fecha date,
    hora_entrada time,
    hora_salida time
);

CREATE TYPE estado AS ENUM ('aprobado', 'rechazado', 'pendiente');

CREATE TABLE IF NOT EXISTS JUSTIFICACIONES (
    id_justificacion serial,
    id_usuario int,
    fecha date,
    motivo text,
    estado estado,
    fecha_solicitud timestamp
);

CREATE TABLE IF NOT EXISTS TURNOS (
    id_turno serial,
    nombre_turno varchar,
    hora_inicio time,
    hora_fin time
);

CREATE TABLE IF NOT EXISTS TURNOS_ASIGNADOS (
    id_usuario int,
    id_turno int,
    fecha_inicio date,
    fecha_fin date
);

CREATE TABLE IF NOT EXISTS PERMISOS (
    id_permiso serial,
    id_usuario int,
    fecha date,
    motivo text,
    estado estado
)