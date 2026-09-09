-- Migración 006: bloquear auth_id en movimientos y presupuestos
-- Requiere que la verificación de 005 haya devuelto 0 en ambos conteos.
-- Ejecutar manualmente en el SQL Editor de Supabase.

alter table movimientos
  alter column auth_id set not null;

alter table presupuestos
  alter column auth_id set not null;
