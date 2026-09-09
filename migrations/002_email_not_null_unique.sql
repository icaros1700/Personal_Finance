-- Migración 002: bloquear la columna email de usuarios
-- Requiere que TODAS las filas de usuarios ya tengan un email cargado
-- (paso manual realizado en el Table Editor de Supabase antes de correr esto).
-- Ejecutar manualmente en el SQL Editor de Supabase.

alter table usuarios
  alter column email set not null;

alter table usuarios
  add constraint usuarios_email_key unique (email);
