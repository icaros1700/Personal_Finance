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
def registrar_movimiento(usuario_id, fecha, tipo, categoria, valor, descripcion):
    supabase.table("movimientos").insert({
        "usuario_id": usuario_id,
        "fecha": fecha.isoformat(),  # Convertir fecha a string ISO 8601
        "tipo": tipo,
        "categoria": categoria,
        "valor": valor,
        "descripcion": descripcion
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
    "ingreso": ["Sueldo", "Inversiones", "Ganancias", "Prestamos"],
    "gasto": ["Hogar", "Vehículo", "Alimentación", "Entretenimiento", "Bancos", "Salud"]}

tab1, tab2 = st.tabs(["Registros", "Estadisticas"])

# Formulario para registrar movimientos
with tab1:
    st.subheader("📊 Registrar Movimiento")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    tipo = st.selectbox("Tipo", ["ingreso", "gasto"])
    categoria = st.selectbox("Categoría", tipo_categorias[tipo])
    valor = st.number_input("Valor", min_value=0.01, step=0.01)
    descripcion = st.text_input("Descripcion")
    if st.button("Guardar Movimiento"):
        registrar_movimiento(st.session_state.usuario_id, fecha, tipo, categoria, valor, descripcion)
        st.success("Movimiento registrado correctamente")

# Mostrar métricas
with tab2:
    st.subheader("📈 Resumen Financiero")
    response = supabase.table("movimientos").select("tipo, valor, fecha, categoria").eq("usuario_id", st.session_state.usuario_id).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        total_ingresos = df[df["tipo"] == "ingreso"]["valor"].sum()
        total_gastos = df[df["tipo"] == "gasto"]["valor"].sum()
        balance = total_ingresos - total_gastos
        st.metric("💵 Total Ingresos", f"${total_ingresos:.2f}")
        st.metric("💸 Total Gastos", f"${total_gastos:.2f}")
        st.metric("🔹 Balance", f"${balance:.2f}")

        # Gráfico de gastos por categoría
        fig = px.pie(df[df["tipo"] == "gasto"], names="categoria", values="valor", title="Gastos por Categoría")
        st.plotly_chart(fig)

        # Gráfico de tendencias semanales
        df["fecha"] = pd.to_datetime(df["fecha"])
        df_weekly = df.groupby(pd.Grouper(key="fecha", freq="W"))["valor"].sum().reset_index()
        fig2 = px.line(df_weekly, x="fecha", y="valor", title="Tendencia de Gastos")
        st.plotly_chart(fig2)
    else:
        st.warning("No hay movimientos registrados.")

# Botón de cierre de sesión
if st.button("Cerrar sesión"):
    st.session_state.usuario_id = None
    st.rerun()