# Aplicación de Finanzas Personales

Una aplicación web para gestionar finanzas personales, construida con Python, Streamlit y PostgreSQL.

## Características

- ✅ Registro e inicio de sesión de usuarios
- 📊 Dashboard con gráficos y estadísticas
- 💰 Registro de ingresos y gastos
- 📋 Múltiples categorías predefinidas
- 📈 Visualización de datos históricos
- 🔒 Datos personalizados por usuario

## Requisitos

- Python 3.8+
- PostgreSQL
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


3. Ejecutar la aplicación:
```bash
streamlit run finance.py
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

Para la base de datos, se recomienda usar:
- [Supabase](https://supabase.com)
- [Railway PostgreSQL](https://railway.app)
- [Heroku Postgres](https://www.heroku.com/postgres)

## Estructura del Proyecto

```
personal_finance_app/
├── app.py              # Aplicación principal Streamlit
├── init_db.py         # Inicialización de la base de datos
├── requirements.txt   # Dependencias del proyecto
├── .env              # Variables de entorno (no incluido en git)
└── .gitignore        # Archivos ignorados por git
```

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.