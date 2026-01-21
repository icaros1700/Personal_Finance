import os
# Configuración para evitar errores en algunos entornos de despliegue
os.environ["STREAMLIT_WATCHDOG"] = "false"  

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from supabase import create_client
from passlib.hash import bcrypt

# --- CONFIGURACIÓN SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error configurando Supabase: {e}. Revisa tus secrets.")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Finanzas Personales Pro", page_icon="💰", layout="wide")

# --- FUNCIONES DE BASE DE DATOS ---
def registrar_usuario(nombre, usuario, password):
    hashed_password = bcrypt.hash(password)
    try:
        response = supabase.table("usuarios").insert({
            "nombre": nombre,
            "usuario": usuario,
            "password": hashed_password
        }).execute()
        return response
    except Exception as e:
        return None

def autenticar_usuario(usuario, password):
    try:
        response = supabase.table("usuarios").select("id, password").eq("usuario", usuario).execute()
        if response.data:
            stored_password = response.data[0]["password"]
            if bcrypt.verify(password, stored_password):
                return response.data[0]["id"]
    except Exception as e:
        pass
    return None

def registrar_movimiento(usuario_id, fecha, tipo, categoria, valor, descripcion, forma_pago):
    supabase.table("movimientos").insert({
        "usuario_id": usuario_id,
        "fecha": fecha.isoformat(),
        "tipo": tipo,
        "categoria": categoria,
        "valor": valor,
        "descripcion": descripcion,
        "forma_pago": forma_pago
    }).execute()

# --- GESTIÓN DE SESIÓN ---
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

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
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Crear Cuenta"):
                    response = registrar_usuario(nombre, usuario, password)
                    if response:
                        st.success("¡Registro exitoso! Por favor inicia sesión.")
                    else:
                        st.error("Error: El usuario ya existe o hubo un problema.")

        else: # Login
            with st.form("login"):
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar"):
                    user_id = autenticar_usuario(usuario, password)
                    if user_id:
                        st.session_state.usuario_id = user_id
                        st.success("Bienvenido")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
    st.stop()

# --- APLICACIÓN PRINCIPAL (SOLO SI ESTÁ LOGUEADO) ---

# Categorías Maestras
tipo_categorias = {
    "ingreso": ["Sueldo", "Inversiones", "Ganancias", "Prestamos", "Retornos", "Otros Ingresos"],
    "gasto": ["Hogar", "Vehículo", "Alimentación", "Entretenimiento", "Bancos", "Salud", "Educacion", "Imprevistos", "Ropa", "Gym", "Transporte", "Servicios", "Regalos", "Ahorro", "Inversion"]
}

# Título y Logout
col_head1, col_head2 = st.columns([4,1])
with col_head1:
    st.title("📊 Dashboard Financiero")
with col_head2:
    if st.button("Cerrar Sesión"):
        st.session_state.usuario_id = None
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
        
        # Selector de Tipo FUERA del form
        tipo = st.radio("Tipo de Movimiento", ["ingreso", "gasto"], horizontal=True)
        cat_list = tipo_categorias.get(tipo, ["General"])

        with st.form("frm_movimiento", clear_on_submit=True):
            fecha = st.date_input("Fecha", value=datetime.date.today())
            categoria = st.selectbox("Categoría", cat_list)
            valor = st.number_input("Valor ($)", min_value=0.01, step=10.0)
            descripcion = st.text_input("Descripción")
            forma_pago = st.selectbox("Pago", ["Efectivo", "Tarjeta Crédito", "Tarjeta Débito", "Transferencia"])
            
            if st.form_submit_button("💾 Guardar"):
                registrar_movimiento(st.session_state.usuario_id, fecha, tipo, categoria, valor, descripcion, forma_pago)
                st.toast("Movimiento guardado exitosamente!", icon="✅")
                st.rerun() 

    # --- PARTE 2: TABLA DE GESTIÓN (ELIMINAR) ---
    with col_reg2:
        st.subheader("📝 Últimos Movimientos (Gestión)")
        
        # Cargar últimos 20 movimientos
        resp = supabase.table("movimientos").select("*").eq("usuario_id", st.session_state.usuario_id).order("fecha", desc=True).limit(20).execute()
        df_gest = pd.DataFrame(resp.data)
        
        if not df_gest.empty:
            df_gest["fecha"] = pd.to_datetime(df_gest["fecha"]).dt.date

            st.dataframe(
                df_gest[["fecha", "tipo", "categoria", "valor", "descripcion"]], 
                use_container_width=True, 
                height=350,
                hide_index=True
            )
            
            st.markdown("##### 🗑️ Eliminar un registro")
            col_del1, col_del2 = st.columns([3, 1])
            
            with col_del1:
                opciones_borrar = {f"{row['fecha']} - {row['categoria']}: {row['descripcion']} (${row['valor']})": row['id'] for index, row in df_gest.iterrows()}
                seleccion_borrar = st.selectbox("Selecciona para eliminar", list(opciones_borrar.keys()), label_visibility="collapsed")
            
            with col_del2:
                if st.button("Eliminar ❌", type="primary"):
                    if seleccion_borrar:
                        id_a_borrar = opciones_borrar[seleccion_borrar]
                        try:
                            supabase.table("movimientos").delete().eq("id", id_a_borrar).execute()
                            st.toast("Registro eliminado.", icon="🗑️")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No hay movimientos recientes.")

# --------------------------------------------------------------------------------
# TAB 2: ESTADÍSTICAS (FILTROS Y GRÁFICOS CORREGIDOS)
# --------------------------------------------------------------------------------
with tab2:
    # 1. Cargar TODOS los datos
    response = supabase.table("movimientos").select("*").eq("usuario_id", st.session_state.usuario_id).execute()
    df = pd.DataFrame(response.data)

    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["año"] = df["fecha"].dt.year
        df["mes_num"] = df["fecha"].dt.month
        
        meses_es = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        df["mes"] = df["mes_num"].map(meses_es)

        # --- FILTROS ---
        with st.container():
            col_tools1, col_tools2 = st.columns(2)
            
            years_opt = ["Todos"] + sorted(df["año"].unique().tolist(), reverse=True)
            sel_year = col_tools1.selectbox("📅 Filtrar Año", years_opt)
            
            months_opt = ["Todos"] + list(meses_es.values())
            sel_month = col_tools2.selectbox("📅 Filtrar Mes", months_opt)

            # Lógica de Filtrado
            df_filtered = df.copy()
            if sel_year != "Todos":
                df_filtered = df_filtered[df_filtered["año"] == sel_year]
            if sel_month != "Todos":
                month_idx = [k for k, v in meses_es.items() if v == sel_month][0]
                df_filtered = df_filtered[df_filtered["mes_num"] == month_idx]
            
        st.divider()

        if df_filtered.empty:
            st.warning("No hay datos para el periodo seleccionado.")
        else:
            # --- KPIs ---
            total_ing = df_filtered[df_filtered["tipo"] == "ingreso"]["valor"].sum()
            total_gas = df_filtered[df_filtered["tipo"] == "gasto"]["valor"].sum()
            balance = total_ing - total_gas

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Ingresos", f"${total_ing:,.2f}", delta="Entradas")
            kpi2.metric("Gastos", f"${total_gas:,.2f}", delta="-Salidas", delta_color="inverse")
            kpi3.metric("Ahorro Neto", f"${balance:,.2f}", delta_color="normal" if balance >= 0 else "inverse")
            
            tasa_ahorro = (balance / total_ing * 100) if total_ing > 0 else 0
            kpi4.metric("Tasa de Ahorro", f"{tasa_ahorro:.1f}%", help="% de ingresos retenidos.")

            # --- GRÁFICOS FILA 1 ---
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
                    st.info("No hay gastos registrados en 'Bancos' para este periodo.")

            st.divider()
            
            # --- FILA 2: GRÁFICO SEMANAL Y TABLA RANKING ---
            g_col3, g_col4 = st.columns([2, 1])

            with g_col3:
                st.markdown("#### 📆 Tendencia Semanal")
                df_gastos_all = df_filtered[df_filtered["tipo"] == "gasto"].copy()
                if not df_gastos_all.empty:
                    # CORRECCIÓN DE ERROR AQUÍ:
                    # Agrupamos por inicio de semana (esto ya devuelve timestamp)
                    df_gastos_all["inicio_semana"] = df_gastos_all["fecha"].dt.to_period('W').dt.start_time
                    df_semanal = df_gastos_all.groupby("inicio_semana")["valor"].sum().reset_index()
                    
                    # Eliminada la línea conflictiva: df_semanal["inicio_semana"].dt.to_timestamp()
                    
                    fig_line = px.line(df_semanal, x="inicio_semana", y="valor", markers=True)
                    fig_line.update_traces(line_color='#E74C3C', line_width=3)
                    fig_line.update_layout(xaxis_title="Semana", yaxis_title="Total Gastado", 
                                         margin=dict(t=10, b=0, l=0, r=0))
                    
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
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Sin datos.")

    else:
        st.info("Aún no tienes movimientos registrados.")

# --------------------------------------------------------------------------------
# TAB 3: PRESUPUESTO
# --------------------------------------------------------------------------------
with tab3:
    st.subheader("🏦 Control de Metas")
    
    resp = supabase.table("movimientos").select("fecha, tipo, categoria, valor").eq("usuario_id", st.session_state.usuario_id).execute()
    df_mov = pd.DataFrame(resp.data)
    
    if df_mov.empty:
        st.info("Registra movimientos para configurar presupuestos.")
    else:
        df_mov["fecha"] = pd.to_datetime(df_mov["fecha"])
        años_db = sorted(df_mov["fecha"].dt.year.unique().tolist(), reverse=True)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            anio_sel = st.selectbox("Configurar Año", años_db)
        
        meta_resp = supabase.table("presupuestos").select("*").eq("usuario_id", st.session_state.usuario_id).eq("anio", anio_sel).execute()
        meta_data = meta_resp.data[0] if meta_resp.data else {}
        
        val_ahorro = meta_data.get("ahorro_meta", 0.0)
        val_inversion = meta_data.get("inversion_meta", 0.0)

        with col_p2:
            with st.form("frm_metas"):
                n_ahorro = st.number_input("Meta Ahorro Anual", value=float(val_ahorro), step=100.0)
                n_inversion = st.number_input("Meta Inversión Anual", value=float(val_inversion), step=100.0)
                if st.form_submit_button("Actualizar Metas"):
                    supabase.table("presupuestos").upsert({
                        "usuario_id": st.session_state.usuario_id,
                        "anio": anio_sel,
                        "ahorro_meta": n_ahorro,
                        "inversion_meta": n_inversion
                    }).execute()
                    st.success("Metas actualizadas.")
                    st.rerun()

        # Cálculos
        df_anio = df_mov[df_mov["fecha"].dt.year == anio_sel]
        
        real_ahorro = df_anio[(df_anio["categoria"] == "Ahorro")]["valor"].sum()
        real_inversion = df_anio[(df_anio["categoria"] == "Inversion")]["valor"].sum()
        
        def calc_pct(real, meta):
            return min(real/meta, 1.0) if meta > 0 else 0

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Ahorro Real vs Meta", f"${real_ahorro:,.2f}", f"Meta: ${n_ahorro:,.2f}")
            st.progress(calc_pct(real_ahorro, n_ahorro))
        with col_m2:
            st.metric("Inversión Real vs Meta", f"${real_inversion:,.2f}", f"Meta: ${n_inversion:,.2f}")
            st.progress(calc_pct(real_inversion, n_inversion))

# --------------------------------------------------------------------------------
# TAB 4: PROYECCIÓN (FUTURO)
# --------------------------------------------------------------------------------
with tab4:
    st.header("🔮 Proyección de Libertad Financiera")
    st.markdown("Simula el crecimiento de tu patrimonio con interés compuesto.")

    # 1. Calcular Capital Actual (Histórico)
    resp_all = supabase.table("movimientos").select("categoria, valor").eq("usuario_id", st.session_state.usuario_id).execute()
    df_all = pd.DataFrame(resp_all.data)
    
    capital_actual = 0.0
    if not df_all.empty:
        capital_actual = df_all[df_all["categoria"].isin(["Ahorro", "Inversion"])]["valor"].sum()
    
    col_proj_izq, col_proj_der = st.columns([1, 2])

    with col_proj_izq:
        st.markdown("### ⚙️ Parámetros")
        st.info(f"💰 Capital Actual (Histórico): **${capital_actual:,.2f}**")
        
        edad_actual = st.number_input("Tu edad actual", min_value=18, max_value=90, value=30)
        edad_retiro = st.number_input("Edad de retiro", min_value=edad_actual+1, max_value=100, value=60)
        tasa_interes = 8.0 # Fijo al 8%
        st.caption(f"Tasa de Interés anual (estimada): **{tasa_interes}%**")
        
        aporte_mensual = st.number_input("Aporte mensual extra (Opcional)", min_value=0.0, step=50.0)

    with col_proj_der:
        st.markdown("### 🚀 Resultados Estimados")
        anos = edad_retiro - edad_actual
        meses = anos * 12
        tasa_mensual = (tasa_interes / 100) / 12
        
        if anos > 0:
            vf_capital = capital_actual * ((1 + tasa_mensual) ** meses)
            vf_aportes = 0
            if aporte_mensual > 0:
                vf_aportes = aporte_mensual * ( ((1 + tasa_mensual) ** meses - 1) / tasa_mensual )
            
            valor_futuro = vf_capital + vf_aportes
            
            st.metric(label=f"Capital a los {edad_retiro} años", value=f"${valor_futuro:,.2f}")
            
            ganancia_intereses = valor_futuro - (capital_actual + (aporte_mensual * meses))
            st.success(f"¡Intereses generados: **${ganancia_intereses:,.2f}**!")

            data_points = []
            saldo = capital_actual
            for i in range(anos + 1):
                data_points.append({"Edad": edad_actual + i, "Saldo": saldo})
                saldo = saldo * (1 + (tasa_interes/100)) + (aporte_mensual * 12)
            
            df_proj = pd.DataFrame(data_points)
            
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