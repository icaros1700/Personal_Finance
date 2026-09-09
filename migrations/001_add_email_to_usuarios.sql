-- Migración 001: agregar columna email a usuarios
-- Paso previo a la migración de autenticación hacia Supabase Auth.
-- Ejecutar manualmente en el SQL Editor de Supabase.

alter table usuarios
  add column if not exists email text;

-- Nota: se deja nullable y sin unique constraint todavía.
-- Una vez que todos los usuarios tengan su email cargado (paso manual,
-- fuera de este script), se debe agregar:
--   alter table usuarios alter column email set not null;
--   alter table usuarios add constraint usuarios_email_key unique (email);
-- antes de proceder a crear las cuentas en Supabase Auth.
