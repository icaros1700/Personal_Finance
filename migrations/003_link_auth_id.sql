-- Migración 003: vincular usuarios con las cuentas creadas en Supabase Auth
-- Requiere que ya existan las cuentas en Authentication > Users (paso manual previo),
-- con el mismo email que usuarios.email.
-- Ejecutar manualmente en el SQL Editor de Supabase.

-- 1) Columna para guardar el UUID de auth.users
alter table usuarios
  add column if not exists auth_id uuid;

-- 2) Poblar auth_id cruzando por email
update usuarios u
set auth_id = a.id
from auth.users a
where a.email = u.email;

-- 3) Verificación: esta consulta debe devolver 0 filas.
-- Si devuelve alguna, significa que ese usuario existe en la tabla `usuarios`
-- pero no tiene una cuenta creada todavía en Authentication > Users con el
-- mismo email (o el email no coincide exactamente, revisar mayúsculas/espacios).
select id, nombre, usuario, email
from usuarios
where auth_id is null;
