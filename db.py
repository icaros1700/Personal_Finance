import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def restaurar_sesion(supabase):
    # Streamlit recrea el script (y con st.cache_resource, reutiliza el mismo
    # cliente) en cada rerun, pero el objeto Client no persiste la sesión de
    # auth entre procesos/workers. Si no se restaura explícitamente, las
    # queries viajan sin token y RLS las rechaza en silencio (0 filas).
    if not st.session_state.get("sb_session"):
        return
    try:
        supabase.auth.set_session(
            access_token=st.session_state.sb_session["access_token"],
            refresh_token=st.session_state.sb_session["refresh_token"],
        )
    except Exception:
        st.session_state.sb_session = None
        st.session_state.usuario_id = None


def registrar_usuario(supabase, nombre, email, password):
    try:
        auth_response = supabase.auth.sign_up({"email": email, "password": password})
        if not auth_response.user:
            return None
        supabase.table("usuarios").insert({
            "auth_id": auth_response.user.id,
            "nombre": nombre,
            "email": email
        }).execute()
        return auth_response
    except Exception:
        return None


def autenticar_usuario(supabase, email, password):
    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if auth_response.user and auth_response.session:
            st.session_state.sb_session = {
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
            }
            return auth_response.user.id
    except Exception:
        pass
    return None


def cerrar_sesion(supabase):
    supabase.auth.sign_out()
    st.session_state.usuario_id = None
    st.session_state.sb_session = None


def registrar_movimiento(supabase, auth_id, fecha, tipo, categoria, valor, descripcion, forma_pago):
    try:
        supabase.table("movimientos").insert({
            "auth_id": auth_id,
            "fecha": fecha.isoformat(),
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "descripcion": descripcion,
            "forma_pago": forma_pago
        }).execute()
        return True
    except Exception as e:
        st.error(f"No se pudo guardar el movimiento: {e}")
        return False


def actualizar_movimiento(supabase, movimiento_id, fecha, tipo, categoria, valor, descripcion, forma_pago):
    try:
        supabase.table("movimientos").update({
            "fecha": fecha.isoformat(),
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "descripcion": descripcion,
            "forma_pago": forma_pago
        }).eq("id", movimiento_id).execute()
        return True
    except Exception as e:
        st.error(f"No se pudo actualizar el movimiento: {e}")
        return False


def eliminar_movimiento(supabase, movimiento_id):
    try:
        supabase.table("movimientos").delete().eq("id", movimiento_id).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def obtener_movimientos(supabase, auth_id, columnas="*", order_by_fecha=False):
    try:
        query = supabase.table("movimientos").select(columnas).eq("auth_id", auth_id)
        if order_by_fecha:
            query = query.order("fecha", desc=True)
        resp = query.execute()
        return resp.data
    except Exception as e:
        st.error(f"No se pudieron cargar los movimientos: {e}")
        return []


def obtener_meta_presupuesto(supabase, auth_id, anio):
    try:
        resp = supabase.table("presupuestos").select("*").eq("auth_id", auth_id).eq("anio", anio).execute()
        return resp.data[0] if resp.data else {}
    except Exception as e:
        st.error(f"No se pudieron cargar las metas de presupuesto: {e}")
        return {}


def guardar_meta_presupuesto(supabase, auth_id, anio, ahorro_meta, inversion_meta):
    try:
        supabase.table("presupuestos").upsert({
            "auth_id": auth_id,
            "anio": anio,
            "ahorro_meta": ahorro_meta,
            "inversion_meta": inversion_meta
        }, on_conflict="auth_id,anio").execute()
        return True
    except Exception as e:
        st.error(f"No se pudieron actualizar las metas: {e}")
        return False
