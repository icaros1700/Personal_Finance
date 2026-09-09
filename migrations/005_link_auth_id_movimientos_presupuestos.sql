-- Migración 005: propagar auth_id a movimientos y presupuestos
-- Requiere que usuarios.auth_id ya esté poblado y bloqueado (migración 004).
-- Ejecutar manualmente en el SQL Editor de Supabase.

-- 1) Columnas nuevas
alter table movimientos
  add column if not exists auth_id uuid;

alter table presupuestos
  add column if not exists auth_id uuid;

-- 2) Poblar cruzando por el usuario_id (int4) viejo contra usuarios.id
update movimientos m
set auth_id = u.auth_id
from usuarios u
where u.id = m.usuario_id;

update presupuestos p
set auth_id = u.auth_id
from usuarios u
where u.id = p.usuario_id;

-- 3) Verificación: ambas consultas deben devolver 0 filas.
select count(*) as movimientos_sin_auth_id
from movimientos
where auth_id is null;

select count(*) as presupuestos_sin_auth_id
from presupuestos
where auth_id is null;
