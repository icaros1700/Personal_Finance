-- Migración 007: activar RLS y crear policies basadas en auth.uid()
-- Ejecutar manualmente en el SQL Editor de Supabase.
-- Requiere que usuarios/movimientos/presupuestos ya tengan auth_id poblado
-- y bloqueado (migraciones 004 y 006).

-- ── usuarios ──────────────────────────────────────────────
alter table usuarios enable row level security;

create policy "usuarios: select propio"
on usuarios for select
using (auth.uid() = auth_id);

create policy "usuarios: update propio"
on usuarios for update
using (auth.uid() = auth_id);

-- Sin policy de insert/delete: el alta de usuarios pasa a manejarse
-- por supabase.auth.sign_up(), no por inserts directos a esta tabla.

-- ── movimientos ───────────────────────────────────────────
alter table movimientos enable row level security;

create policy "movimientos: select propio"
on movimientos for select
using (auth.uid() = auth_id);

create policy "movimientos: insert propio"
on movimientos for insert
with check (auth.uid() = auth_id);

create policy "movimientos: update propio"
on movimientos for update
using (auth.uid() = auth_id);

create policy "movimientos: delete propio"
on movimientos for delete
using (auth.uid() = auth_id);

-- ── presupuestos ──────────────────────────────────────────
alter table presupuestos enable row level security;

create policy "presupuestos: select propio"
on presupuestos for select
using (auth.uid() = auth_id);

create policy "presupuestos: insert propio"
on presupuestos for insert
with check (auth.uid() = auth_id);

create policy "presupuestos: update propio"
on presupuestos for update
using (auth.uid() = auth_id);

create policy "presupuestos: delete propio"
on presupuestos for delete
using (auth.uid() = auth_id);
