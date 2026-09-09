-- Migración 008: constraint UNIQUE(auth_id, anio) en presupuestos
-- Necesario porque finance.py hace upsert() sobre presupuestos usando
-- (usuario_id, anio) como llave de conflicto; al migrar el código a auth_id
-- el upsert necesita un constraint UNIQUE equivalente sobre la columna nueva.
-- Ejecutar manualmente en el SQL Editor de Supabase.

alter table presupuestos
  add constraint presupuestos_auth_id_anio_key unique (auth_id, anio);

-- Nota: se deja el constraint viejo presupuestos_usuario_id_anio_key y la
-- columna usuario_id sin tocar por ahora (limpieza de columnas legacy
-- pendiente para más adelante, junto con la columna password de usuarios).
