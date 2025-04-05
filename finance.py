import streamlit as st
import psycopg2
from supabase import create_client
from passlib.hash import bcrypt
import pandas as pd
import plotly.express as px
import datetime

# Conexion supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración inicial de la página
st.set_page_config(page_title="Finanzas Personales", page_icon="💰", layout="wide")

# Función para registrar usuarios
def registrar_usuario(nombre, usuario, password):
    hashed_password = bcrypt.hash(password)
    response = supabase.table("usuarios").insert({
        "nombre": nombre,
        "usuario": usuario,
        "password": hashed_password
    }).execute()
    return response

# Función para autenticar usuario
def autenticar_usuario(usuario, password):
    response = supabase.table("usuarios").select("id, password").eq("usuario", usuario).execute()
    if response.data:
        stored_password = response.data[0]["password"]
        if bcrypt.verify(password, stored_password):
            return response.data[0]["id"]
    return None

# Función para registrar movimientos
def registrar_movimiento(usuario_id, fecha, tipo, categoria, valor, descripcion, forma_pago):
    supabase.table("movimientos").insert({
        "usuario_id": usuario_id,
        "fecha": fecha.isoformat(),  # Convertir fecha a string ISO 8601
        "tipo": tipo,
        "categoria": categoria,
        "valor": valor,
        "descripcion": descripcion,
        "forma_pago": forma_pago
    }).execute()

# Interfaz en Streamlit
st.title("💰 Finanzas Personales")

# Manejo de sesión
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

# Mostrar opciones de login/registro solo si no hay sesión iniciada
if st.session_state.usuario_id is None:
    opcion = st.radio("Seleccione una opción", ["Iniciar sesión", "Registrarse"])

    if opcion == "Registrarse":
        with st.form("register"):
            nombre = st.text_input("Nombre Completo")
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Registrarse"):
                response = registrar_usuario(nombre, usuario, password)
                if response and hasattr(response, "error") and response.error:
                    st.error("Error al registrar usuario")
                else:
                    st.success("Usuario registrado con éxito. Ahora puede iniciar sesión.")
        st.stop()

    # Formulario de autenticación
    with st.form("login"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Iniciar sesión"):
            user_id = autenticar_usuario(usuario, password)
            if user_id:
                st.session_state.usuario_id = user_id
                st.success("Inicio de sesión exitoso")
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# Categorías predefinidas
tipo_categorias = {
    "ingreso": ["Sueldo", "Inversiones", "Ganancias", "Prestamos", "Retornos"],
    "gasto": ["Hogar", "Vehículo", "Alimentación", "Entretenimiento", "Bancos", "Salud", "Educacion", "Imprevistos", "Ropa", "Gym", "Transporte", "Servicios", "Regalos"]}

tab1, tab2 = st.tabs(["Registros", "Estadisticas"])

# Formulario para registrar movimientos
with tab1:
    st.subheader("📊 Registrar Movimiento")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    tipo = st.selectbox("Tipo", ["ingreso", "gasto"])
    categoria = st.selectbox("Categoría", tipo_categorias[tipo])
    valor = st.number_input("Valor", min_value=0.01, step=0.01)
    descripcion = st.text_input("Descripcion")
    forma_pago = st.selectbox("Forma Pago", ["Efectivo","Tarjeta1", "Tarjeta2", "Tarjeta3", "Cuenta1", "Cuenta2", "Cuenta3"])
    if st.button("Guardar Movimiento"):
        registrar_movimiento(st.session_state.usuario_id, fecha, tipo, categoria, valor, descripcion, forma_pago)
        st.success("Movimiento registrado correctamente")

# Mostrar métricas
with tab2:
    st.header("📈 Resumen Financiero")
    response = supabase.table("movimientos").select("fecha, tipo, categoria, valor, descripcion, forma_pago").eq("usuario_id", st.session_state.usuario_id).execute()
    df = pd.DataFrame(response.data)

    detalles = df.copy()

    detalles["fecha"] = pd.to_datetime(detalles["fecha"]).dt.date

    with st.expander("📄 Ver detalle de movimientos"):
        st.dataframe(detalles)


    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        total_ingresos = df[df["tipo"] == "ingreso"]["valor"].sum()
        total_gastos = df[df["tipo"] == "gasto"]["valor"].sum()
        balance = total_ingresos - total_gastos

        # Métricas principales
        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Ingresos", f"${total_ingresos:,.2f}")
        col2.metric("💸 Total Gastos", f"${total_gastos:,.2f}")
        col3.metric("🔹 Balance", f"${balance:,.2f}")

        # Métricas del mes y semana actual
        hoy = pd.Timestamp.today()
        semana_actual = hoy.isocalendar().week
        mes_actual = hoy.month
        anio_actual = hoy.year

        gastos_semana = df[
            (df["tipo"] == "gasto") &
            (df["fecha"].dt.isocalendar().week == semana_actual) &
            (df["fecha"].dt.year == anio_actual)
        ]["valor"].sum()

        gastos_mes = df[
            (df["tipo"] == "gasto") &
            (df["fecha"].dt.month == mes_actual) &
            (df["fecha"].dt.year == anio_actual)
        ]["valor"].sum()

        col4, col5 = st.columns(2)
        col4.metric("📆 Gastos del Mes", f"${gastos_mes:,.2f}")
        col5.metric("🗓️ Gastos de la Semana", f"${gastos_semana:,.2f}")

        # Tablas por categoría
        st.subheader("📊 Gastos Totales por Categoría")

        # Filtrar solo los gastos
        df_gastos = df[df["tipo"] == "gasto"]

        # Agrupar y sumar por categoría
        gastos_categoria = df_gastos.groupby("categoria")["valor"].sum().reset_index()

        # Formatear los valores con separador de miles y signo de moneda
        gastos_categoria["valor"] = gastos_categoria["valor"].apply(lambda x: f"${x:,.2f}")

        # Mostrar en Streamlit
        st.dataframe(gastos_categoria)

        


        # Gráficos
        col1, col2 = st.columns(2)

        with col1:
            gastos_por_categoria = df[df["tipo"] == "gasto"].groupby("categoria")["valor"].sum().reset_index()

            fig = px.bar(
            gastos_por_categoria,
            x="categoria",
            y="valor",
            color="categoria",  # 🟢 Colores diferentes por categoría
            title="Gastos por Categoría",
            text_auto=True)

            fig.update_layout(
            xaxis_title="Categoría",
            yaxis_title="Valor",
            showlegend=False,  # 🔵 Oculta la leyenda si no la necesitas
            plot_bgcolor='rgba(0,0,0,0)',  # Fondo del gráfico transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fondo exterior transparente
            font=dict(size=14),)

            # Opcional: cambia el color de las barras manualmente
            # fig.update_traces(marker_color=['#FF6361', '#58508D', '#FFA600'])

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            df_gastos = df[df["tipo"] == "gasto"]
            df_weekly = df_gastos.groupby(pd.Grouper(key="fecha", freq="W"))["valor"].sum().reset_index()
            fig2 = px.line(df_weekly, x="fecha", y="valor", title="Tendencia Semanal de Gastos")
            fig2.update_layout(xaxis_title="Semana", yaxis_title="Gastos")
            st.plotly_chart(fig2, use_container_width=True)
        
        col3, col4 = st.columns(2)

        with col3:
            gastos_por_forma = df[df["tipo"] == "gasto"].groupby("forma_pago")["valor"].sum().reset_index()

            fig = px.bar(
            gastos_por_forma,
            x="forma_pago",
            y="valor",
            color="forma_pago",  # 🟢 Colores diferentes por categoría
            title="Totales Forma Pago",
            text_auto=True)

            fig.update_layout(
            xaxis_title="Forma de Pago",
            yaxis_title="Valor",
            showlegend=False,  # 🔵 Oculta la leyenda si no la necesitas
            plot_bgcolor='rgba(0,0,0,0)',  # Fondo del gráfico transparente
            paper_bgcolor='rgba(0,0,0,0)',  # Fondo exterior transparente
            font=dict(size=14),)

            # Opcional: cambia el color de las barras manualmente
            # fig.update_traces(marker_color=['#FF6361', '#58508D', '#FFA600'])

            st.plotly_chart(fig, use_container_width=True)


    else:
        st.warning("No hay movimientos registrados.")

# Botón de cierre de sesión
if st.button("Cerrar sesión"):
    st.session_state.usuario_id = None
    st.rerun()