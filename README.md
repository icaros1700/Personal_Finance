# Aplicación de Finanzas Personales

Una aplicación web para gestionar finanzas personales, construida con Python, Streamlit y Supabase (Postgres).

## Características

- ✅ Registro e inicio de sesión de usuarios
- 📊 Dashboard con gráficos y estadísticas
- 💰 Registro de ingresos y gastos
- 📋 Múltiples categorías predefinidas
- 📈 Visualización de datos históricos
- 🎯 Presupuesto anual con metas de ahorro e inversión
- 🔮 Proyección de patrimonio con interés compuesto
- 🔒 Datos personalizados por usuario

## Requisitos

- Python 3.8+
- Una cuenta y proyecto en [Supabase](https://supabase.com) con las tablas `usuarios`, `movimientos` y `presupuestos`
- Las dependencias listadas en `requirements.txt`

## Configuración

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd finance_app
```

2. Crear un entorno virtual e instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configurar las credenciales de Supabase en `.streamlit/secrets.toml` (este archivo no se sube a git):
```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-clave-anon-o-service"
```

4. Ejecutar la aplicación:
```bash
streamlit run finance.py
```

## Despliegue

La aplicación está lista para ser desplegada en:

- [Streamlit Cloud](https://streamlit.io/cloud)
- [Heroku](https://www.heroku.com)
- [Railway](https://railway.app)

La base de datos se gestiona en [Supabase](https://supabase.com); en el panel de despliegue hay que configurar `SUPABASE_URL` y `SUPABASE_KEY` como secretos (equivalentes al `.streamlit/secrets.toml` local).

## Estructura del Proyecto

```
finance_app/
├── finance.py              # Aplicación principal Streamlit (login, dashboard, tabs)
├── requirements.txt        # Dependencias del proyecto
├── .streamlit/secrets.toml # Credenciales de Supabase (no incluido en git)
└── .gitignore               # Archivos ignorados por git
```

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.