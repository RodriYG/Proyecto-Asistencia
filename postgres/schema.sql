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

-- CREATE INDEX code_index ON USUARIO (rut);

-- CREATE TABLE IF NOT EXISTS ASISTENCIAS (
--     id_turno
-- )