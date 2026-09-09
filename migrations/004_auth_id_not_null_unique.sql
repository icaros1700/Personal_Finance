-- Migración 004: bloquear la columna auth_id de usuarios
-- Requiere que la verificación de 003 haya devuelto 0 filas (todos los
-- usuarios ya vinculados a una cuenta de Supabase Auth).
-- Ejecutar manualmente en el SQL Editor de Supabase.

alter table usuarios
  alter column auth_id set not null;

alter table usuarios
  add constraint usuarios_auth_id_key unique (auth_id);
