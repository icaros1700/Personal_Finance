import os

# Configuración para evitar errores en algunos entornos de despliegue
os.environ["STREAMLIT_WATCHDOG"] = "false"

import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import calculos
import db
from config import FORMAS_PAGO, MESES_ES, TIPO_CATEGORIAS

# --- CONFIGURACIÓN DE PÁGINA ---
# set_page_config debe ser el primer comando de Streamlit del script.
st.set_page_config(page_title="Finanzas Personales Pro", page_icon="💰", layout="wide")

# --- CONFIGURACIÓN SUPABASE ---
try:
    supabase = db.get_client()
except Exception as e:
    st.error(f"Error configurando Supabase: {e}. Revisa tus secrets.")
    st.stop()

db.restaurar_sesion(supabase)

# --- GESTIÓN DE SESIÓN ---
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "sb_session" not in st.session_state:
    st.session_state.sb_session = None

# --- PANTALLA DE LOGIN / REGISTRO ---
if st.session_state.usuario_id is None:
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
        st.title("💰 Finanzas Personales")
        st.markdown("---")
        opcion = st.radio("Acceso", ["Iniciar sesión", "Registrarse"], horizontal=True)

        if opcion == "Registrarse":
            with st.form("register"):
                nombre = st.text_input("Nombre Completo")
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Crear Cuenta"):
                    exito, cuenta_huerfana = db.registrar_usuario(supabase, nombre, email, password)
                    if exito:
                        st.success("¡Registro exitoso! Por favor inicia sesión.")
                    elif cuenta_huerfana:
                        st.error(
                            "Tu cuenta de acceso se creó, pero hubo un problema guardando tu perfil. "
                            "No vuelvas a registrarte con este email: contacta al administrador para completar el alta."
                        )
                    else:
                        st.error("Error: El usuario ya existe o hubo un problema.")

        else: # Login
            with st.form("login"):
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar"):
                    user_id = db.autenticar_usuario(supabase, email, password)
                    if user_id:
                        st.session_state.usuario_id = user_id
                        st.success("Bienvenido")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
    st.stop()

# --- APLICACIÓN PRINCIPAL (SOLO SI ESTÁ LOGUEADO) ---

# Título y Logout
col_head1, col_head2 = st.columns([4,1])
with col_head1:
    st.title("📊 Dashboard Financiero")
with col_head2:
    if st.button("Cerrar Sesión"):
        db.cerrar_sesion(supabase)
        st.rerun()

# Pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📝 Gestión", "📈 Estadísticas", "🏦 Presupuesto", "🔮 Proyección"])

# --------------------------------------------------------------------------------
# TAB 1: GESTIÓN (REGISTRAR Y ELIMINAR)
# --------------------------------------------------------------------------------
with tab1:
    col_reg1, col_reg2 = st.columns([1, 2])

    # --- PARTE 1: EL FORMULARIO DE REGISTRO ---
    with col_reg1:
        st.subheader("➕ Nuevo")

        # Tipo y Categoría van FUERA del st.form para que la página se
        # actualice instantáneamente al cambiar el Tipo.
        tipo_seleccionado = st.radio("Tipo", ["ingreso", "gasto"], horizontal=True, key="tipo_input")
        lista_categorias = TIPO_CATEGORIAS.get(tipo_seleccionado, ["General"])
        categoria_seleccionada = st.selectbox("Categoría", lista_categorias, key="cat_input")

        with st.form("frm_movimiento", clear_on_submit=True):
            fecha = st.date_input("Fecha", value=datetime.date.today())
            if fecha > datetime.date.today():
                st.caption("⚠️ La fecha es futura. Se guardará igual si continúas.")
            valor = st.number_input("Valor ($)", min_value=0.01, step=10.0)
            descripcion = st.text_input("Descripción")
            forma_pago = st.selectbox("Pago", FORMAS_PAGO)

            if st.form_submit_button("💾 Guardar Movimiento"):
                if db.registrar_movimiento(supabase, st.session_state.usuario_id, fecha, tipo_seleccionado, categoria_seleccionada, valor, descripcion, forma_pago):
                    st.session_state.pagina_gestion = 1
                    st.toast("Movimiento guardado exitosamente!", icon="✅")
                    st.rerun()

    # --- PARTE 2: TABLA DE GESTIÓN (ELIMINAR) ---
    with col_reg2:
        st.subheader("📝 Últimos Movimientos (Gestión)")

        POR_PAGINA = 50
        if "pagina_gestion" not in st.session_state:
            st.session_state.pagina_gestion = 1

        busqueda = st.text_input("🔍 Buscar por descripción o categoría", key="busqueda_gestion")
        if busqueda != st.session_state.get("busqueda_gestion_anterior", ""):
            st.session_state.pagina_gestion = 1
            st.session_state.busqueda_gestion_anterior = busqueda

        with st.spinner("Cargando movimientos..."):
            movimientos, total = db.obtener_movimientos_paginados(
                supabase, st.session_state.usuario_id,
                pagina=st.session_state.pagina_gestion, por_pagina=POR_PAGINA, busqueda=busqueda
            )
        total_paginas = max((total + POR_PAGINA - 1) // POR_PAGINA, 1)

        # Si al eliminar quedó apuntando a una página que ya no existe, retrocedemos.
        if not movimientos and st.session_state.pagina_gestion > 1:
            st.session_state.pagina_gestion = total_paginas
            st.rerun()

        df_gest = pd.DataFrame(movimientos)

        if not df_gest.empty:
            df_gest["fecha"] = pd.to_datetime(df_gest["fecha"]).dt.date

            st.dataframe(
                df_gest[["fecha", "tipo", "categoria", "valor", "descripcion"]],
                use_container_width=True,
                height=350,
                hide_index=True
            )

            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            with col_pag1:
                if st.button("⬅️ Anterior", disabled=st.session_state.pagina_gestion <= 1):
                    st.session_state.pagina_gestion -= 1
                    st.rerun()
            with col_pag2:
                st.markdown(f"<div style='text-align:center'>Página {st.session_state.pagina_gestion} de {total_paginas} ({total} movimientos)</div>", unsafe_allow_html=True)
            with col_pag3:
                if st.button("Siguiente ➡️", disabled=st.session_state.pagina_gestion >= total_paginas):
                    st.session_state.pagina_gestion += 1
                    st.rerun()

            opciones_mov = {f"{row['fecha']} - {row['categoria']}: {row['descripcion']} (${row['valor']})": row['id'] for index, row in df_gest.iterrows()}

            st.markdown("##### ✏️ Editar un registro")
            seleccion_editar = st.selectbox("Selecciona para editar", list(opciones_mov.keys()), label_visibility="collapsed", key="sel_editar")

            if seleccion_editar:
                id_a_editar = opciones_mov[seleccion_editar]
                mov_actual = df_gest[df_gest["id"] == id_a_editar].iloc[0]

                with st.form("frm_editar_movimiento"):
                    e_tipo = st.radio("Tipo", ["ingreso", "gasto"], horizontal=True, index=["ingreso", "gasto"].index(mov_actual["tipo"]))
                    e_categoria = st.selectbox("Categoría", TIPO_CATEGORIAS.get(e_tipo, ["General"]))
                    e_fecha = st.date_input("Fecha", value=mov_actual["fecha"])
                    if e_fecha > datetime.date.today():
                        st.caption("⚠️ La fecha es futura. Se guardará igual si continúas.")
                    e_valor = st.number_input("Valor ($)", min_value=0.01, step=10.0, value=float(mov_actual["valor"]))
                    e_descripcion = st.text_input("Descripción", value=mov_actual["descripcion"])
                    e_forma_pago = st.selectbox("Pago", FORMAS_PAGO, index=FORMAS_PAGO.index(mov_actual["forma_pago"]) if mov_actual["forma_pago"] in FORMAS_PAGO else 0)

                    if st.form_submit_button("💾 Guardar cambios"):
                        if db.actualizar_movimiento(supabase, id_a_editar, e_fecha, e_tipo, e_categoria, e_valor, e_descripcion, e_forma_pago):
                            st.toast("Movimiento actualizado.", icon="✏️")
                            st.rerun()

            st.markdown("##### 🗑️ Eliminar un registro")
            col_del1, col_del2 = st.columns([3, 1])

            with col_del1:
                seleccion_borrar = st.selectbox("Selecciona para eliminar", list(opciones_mov.keys()), label_visibility="collapsed", key="sel_borrar")

            with col_del2:
                if st.button("Eliminar ❌", type="primary"):
                    st.session_state.confirmar_borrado = seleccion_borrar

            if st.session_state.get("confirmar_borrado"):
                st.warning(f"¿Eliminar este registro? **{st.session_state.confirmar_borrado}**")
                col_conf1, col_conf2 = st.columns(2)
                with col_conf1:
                    if st.button("✅ Sí, eliminar", type="primary"):
                        id_a_borrar = opciones_mov.get(st.session_state.confirmar_borrado)
                        st.session_state.confirmar_borrado = None
                        if id_a_borrar and db.eliminar_movimiento(supabase, id_a_borrar):
                            st.toast("Registro eliminado.", icon="🗑️")
                            st.rerun()
                with col_conf2:
                    if st.button("Cancelar"):
                        st.session_state.confirmar_borrado = None
                        st.rerun()
        else:
            st.info("No hay movimientos recientes.")

# --------------------------------------------------------------------------------
# TAB 2: ESTADÍSTICAS (FILTROS, GRAFICOS Y RANKING)
# --------------------------------------------------------------------------------
with tab2:
    with st.spinner("Cargando movimientos..."):
        df = pd.DataFrame(db.obtener_movimientos(supabase, st.session_state.usuario_id))

    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["año"] = df["fecha"].dt.year
        df["mes_num"] = df["fecha"].dt.month
        df["mes"] = df["mes_num"].map(MESES_ES)

        with st.container():
            col_tools1, col_tools2 = st.columns(2)
            years_opt = ["Todos"] + sorted(df["año"].unique().tolist(), reverse=True)
            sel_year = col_tools1.selectbox("📅 Filtrar Año", years_opt)
            months_opt = ["Todos"] + list(MESES_ES.values())
            sel_month = col_tools2.selectbox("📅 Filtrar Mes", months_opt)

            df_filtered = df.copy()
            if sel_year != "Todos":
                df_filtered = df_filtered[df_filtered["año"] == sel_year]
            if sel_month != "Todos":
                month_idx = [k for k, v in MESES_ES.items() if v == sel_month][0]
                df_filtered = df_filtered[df_filtered["mes_num"] == month_idx]

        st.divider()

        if df_filtered.empty:
            st.warning("No hay datos para el periodo seleccionado.")
        else:
            kpis = calculos.calcular_kpis(df_filtered)

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Ingresos", f"${kpis['total_ingresos']:,.2f}", delta="Entradas")
            kpi2.metric("Gastos", f"${kpis['total_gastos']:,.2f}", delta="-Salidas", delta_color="inverse")
            kpi3.metric("Ahorro Neto", f"${kpis['balance']:,.2f}", delta_color="normal" if kpis['balance'] >= 0 else "inverse")
            kpi4.metric("Tasa de Ahorro", f"{kpis['tasa_ahorro']:.1f}%", help="% de ingresos retenidos.")

            g_col1, g_col2 = st.columns([1, 1])

            with g_col1:
                st.markdown("#### 🍩 Gastos por Categoría")
                df_gas = df_filtered[df_filtered["tipo"] == "gasto"]
                if not df_gas.empty:
                    fig_pie = px.pie(df_gas, values="valor", names="categoria", hole=0.4)
                    fig_pie.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Sin gastos.")

            with g_col2:
                st.markdown("#### 🏦 Gastos en Bancos (Mensual)")
                df_bancos = df_filtered[(df_filtered["tipo"] == "gasto") & (df_filtered["categoria"].isin(["Bancos", "bancos"]))]
                if not df_bancos.empty:
                    df_bancos["periodo"] = df_bancos["fecha"].dt.strftime('%Y-%m')
                    df_bancos_agg = df_bancos.groupby("periodo")["valor"].sum().reset_index()
                    fig_banco = px.bar(df_bancos_agg, x="periodo", y="valor",
                                     title="Salidas categoría Bancos",
                                     color_discrete_sequence=["#3498DB"])
                    fig_banco.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig_banco, use_container_width=True)
                else:
                    st.info("No hay gastos registrados en 'Bancos'.")

            st.divider()

            g_col3, g_col4 = st.columns([2, 1])

            with g_col3:
                st.markdown("#### 📆 Tendencia Semanal")
                df_gastos_all = df_filtered[df_filtered["tipo"] == "gasto"].copy()
                if not df_gastos_all.empty:
                    df_gastos_all["inicio_semana"] = df_gastos_all["fecha"].dt.to_period('W').dt.start_time
                    df_semanal = df_gastos_all.groupby("inicio_semana")["valor"].sum().reset_index()
                    fig_line = px.line(df_semanal, x="inicio_semana", y="valor", markers=True)
                    fig_line.update_traces(line_color='#E74C3C', line_width=3)
                    fig_line.update_layout(xaxis_title="Semana", yaxis_title="Total Gastado", margin=dict(t=10, b=0, l=0, r=0))
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("No hay datos.")

            with g_col4:
                st.markdown("#### 🏆 Top Gastos")
                if not df_gastos_all.empty:
                    df_ranking = df_gastos_all.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                    df_ranking["Total"] = df_ranking["valor"].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(
                        df_ranking[["categoria", "Total"]],
                        column_config={"categoria": "Categoría", "Total": "Monto Acumulado"},
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("Sin datos.")

            st.divider()

            g_col5, g_col6 = st.columns([1, 1])

            with g_col5:
                st.markdown("#### Ingresos (Mensual)")
                df_bancos = df_filtered[(df_filtered["tipo"] == "ingreso")]
                if not df_bancos.empty:
                    df_bancos["periodo"] = df_bancos["fecha"].dt.strftime('%Y-%m')
                    df_bancos_agg = df_bancos.groupby("periodo")["valor"].sum().reset_index()
                    fig_banco = px.bar(df_bancos_agg, x="periodo", y="valor",
                                     title="Salidas categoría Ingresos",
                                     color_discrete_sequence=["#3498DB"])
                    fig_banco.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig_banco, use_container_width=True)
                else:
                    st.info("No hay ingresos registrados.")

    else:
        st.info("Aún no tienes movimientos registrados.")

# --------------------------------------------------------------------------------
# TAB 3: PRESUPUESTO
# --------------------------------------------------------------------------------
with tab3:
    st.subheader("🏦 Control de Metas")

    with st.spinner("Cargando movimientos..."):
        df_mov = pd.DataFrame(db.obtener_movimientos(supabase, st.session_state.usuario_id, columnas="fecha, tipo, categoria, valor"))

    if df_mov.empty:
        st.info("Registra movimientos para configurar presupuestos.")
    else:
        df_mov["fecha"] = pd.to_datetime(df_mov["fecha"])
        años_db = sorted(df_mov["fecha"].dt.year.unique().tolist(), reverse=True)

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            anio_sel = st.selectbox("Configurar Año", años_db)

        meta_data = db.obtener_meta_presupuesto(supabase, st.session_state.usuario_id, anio_sel)
        val_ahorro = meta_data.get("ahorro_meta", 0.0)
        val_inversion = meta_data.get("inversion_meta", 0.0)

        with col_p2:
            with st.form("frm_metas"):
                n_ahorro = st.number_input("Meta Ahorro Anual", value=float(val_ahorro), step=100.0)
                n_inversion = st.number_input("Meta Inversión Anual", value=float(val_inversion), step=100.0)
                if st.form_submit_button("Actualizar Metas"):
                    if db.guardar_meta_presupuesto(supabase, st.session_state.usuario_id, anio_sel, n_ahorro, n_inversion):
                        st.success("Metas actualizadas.")
                        st.rerun()

        df_anio = df_mov[df_mov["fecha"].dt.year == anio_sel]
        real_ahorro = df_anio[(df_anio["categoria"] == "Ahorro")]["valor"].sum()
        real_inversion = df_anio[(df_anio["categoria"] == "Inversion")]["valor"].sum()

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Ahorro Real vs Meta", f"${real_ahorro:,.2f}", f"Meta: ${n_ahorro:,.2f}")
            st.progress(calculos.calc_pct(real_ahorro, n_ahorro))
        with col_m2:
            st.metric("Inversión Real vs Meta", f"${real_inversion:,.2f}", f"Meta: ${n_inversion:,.2f}")
            st.progress(calculos.calc_pct(real_inversion, n_inversion))

# --------------------------------------------------------------------------------
# TAB 4: PROYECCIÓN (FUTURO)
# --------------------------------------------------------------------------------
with tab4:
    st.header("🔮 Proyección de Libertad Financiera")
    st.markdown("Simula el crecimiento de tu patrimonio con interés compuesto.")

    with st.spinner("Cargando movimientos..."):
        df_all = pd.DataFrame(db.obtener_movimientos(supabase, st.session_state.usuario_id, columnas="categoria, valor"))

    capital_actual = 0.0
    if not df_all.empty:
        capital_actual = df_all[df_all["categoria"].isin(["Ahorro", "Inversion"])]["valor"].sum()

    col_proj_izq, col_proj_der = st.columns([1, 2])

    with col_proj_izq:
        st.markdown("### ⚙️ Parámetros")
        st.info(f"💰 Capital Actual (Histórico): **${capital_actual:,.2f}**")
        edad_actual = st.number_input("Tu edad actual", min_value=18, max_value=90, value=30)
        edad_retiro = st.number_input("Edad de retiro", min_value=edad_actual+1, max_value=100, value=60)
        tasa_interes = 8.0
        st.caption(f"Tasa de Interés anual: **{tasa_interes}%**")
        aporte_mensual = st.number_input("Aporte mensual extra (Opcional)", min_value=0.0, step=50.0)

    with col_proj_der:
        st.markdown("### 🚀 Resultados Estimados")
        proyeccion = calculos.proyectar_patrimonio(capital_actual, edad_actual, edad_retiro, tasa_interes, aporte_mensual)

        if proyeccion:
            st.metric(label=f"Capital a los {edad_retiro} años", value=f"${proyeccion['valor_futuro']:,.2f}")
            st.success(f"¡Intereses generados: **${proyeccion['ganancia_intereses']:,.2f}**!")

            df_proj = pd.DataFrame(proyeccion["curva"])

            fig_proj = px.line(df_proj, x="Edad", y="Saldo", markers=True, title="Curva de Crecimiento Patrimonial")
            fig_proj.update_traces(line_color="#FFD700", line_width=4)
            fig_proj.update_layout(yaxis_tickformat="$,.0f")
            st.plotly_chart(fig_proj, use_container_width=True)
        else:
            st.warning("Ajusta la edad de retiro.")

# Pie de página
st.markdown("""
    <hr style="margin-top: 3rem; margin-bottom: 1rem;">
    <div style="text-align: center; color: gray;">
        <small>Personal Finance Developed for Everybody by William Ruiz © 2025</small>
    </div>
    """, unsafe_allow_html=True)
