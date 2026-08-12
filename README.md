# JL Mantenimiento

Sistema de recepción y reparación de equipos informáticos y electrónicos.

## Características

- Registro de ingreso de equipos al taller
- Gestión de clientes y equipos
- Diagnóstico técnico con editor enriquecido
- Historial completo de órdenes
- Generación de comprobantes en PDF
- Copias de seguridad

## Requisitos

- Python 3.11 o superior
- PyQt6
- SQLite (incluido con Python)

## Instalación

### Linux

```bash
# Desde repositorios del sistema (Debian/Ubuntu)
sudo apt install python3-pyqt6 python3-sqlalchemy python3-platformdirs python3-pil python3-reportlab python3-matplotlib

# Ejecutar
python3 -m luciotech.main
```

### Windows

```bash
# Con Python instalado
python -m luciotech.main
```

### Entorno virtual (todos los sistemas)

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python -m luciotech.main
```

## Estructura del proyecto

```
luciotech/
├── src/luciotech/
│   ├── main.py           # Punto de entrada
│   ├── app.py            # Configuración de la aplicación
│   ├── config.py         # Constantes y configuración
│   ├── database/         # Modelos y acceso a datos
│   ├── services/         # Lógica de negocio
│   ├── ui/               # Interfaz gráfica
│   ├── reports/          # Generación de PDF
│   └── utils/            # Utilidades
└── tests/
```

## Ubicación de datos

- **Linux:** `~/.local/share/lucio-jl-service-manager/`
- **Windows:** `%APPDATA%\lucio-jl-service-manager\`
- **macOS:** `~/Library/Application Support/lucio-jl-service-manager/`

## Pruebas

```bash
pytest
```

## Licencia

Ver archivo LICENSE.
