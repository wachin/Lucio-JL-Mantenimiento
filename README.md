# JL Mantenimiento

<p align="center">
  <strong>Sistema profesional de recepción y reparación de equipos informáticos y electrónicos</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white" alt="Python 3.11+"/>
  </a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/">
    <img src="https://img.shields.io/badge/UI-PyQt6-green.svg?logo=qt" alt="PyQt6"/>
  </a>
  <a href="https://www.sqlalchemy.org/">
    <img src="https://img.shields.io/badge/DB-SQLAlchemy%202-orange.svg?logo=sqlite" alt="SQLAlchemy 2"/>
  </a>
  <a href="https://github.com/Lucio-JL-Mantenimiento/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/>
  </a>
  <a href="https://github.com/Lucio-JL-Mantenimiento/releases">
    <img src="https://img.shields.io/badge/Version-0.1.0--dev-lightgrey.svg" alt="Version 0.1.0-dev"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?logo=linux&logoColor=white" alt="Platforms"/>
  <img src="https://img.shields.io/badge/SQLite-3-brightgreen?logo=sqlite" alt="SQLite"/>
  <img src="https://img.shields.io/badge/PDF-ReportLab-red?logo=adobeacrobatreader&logoColor=white" alt="ReportLab"/>
  <img src="https://img.shields.io/badge/Images-Pillow-9cf?logo=python" alt="Pillow"/>
  <img src="https://img.shields.io/badge/Tests-pytest-purple?logo=pytest" alt="pytest"/>
</p>

---

## Características

| Módulo | Funcionalidades |
|---|---|
| **Recepción** | Registro de ingreso, datos del cliente y equipo, accesorios rápidos, fotografías desde celular |
| **Órdenes** | Lista avanzada con filtros, búsqueda en tiempo real, doble clic para abrir, papelera |
| **Diagnóstico** | Editor enriquecido tipo Word (negrita, colores, tablas, imágenes, buscar/reemplazar) |
| **Fotografías** | Carga, miniaturas, rotación, clasificación por tipo, vista completa |
| **Historial** | Línea de tiempo de estados y eventos, notas internas, eventos tipificados |
| **Presupuesto** | Conceptos con cálculo automático, pagos, saldo pendiente, impuestos configurables |
| **PDF** | Comprobante de recepción, informe técnico, vista previa, impresión directa |
| **Reportes** | Filtros por fecha/estado, exportación PDF y CSV, resumen económico |
| **Copias de seguridad** | ZIP completo (DB + fotos + config), restaurar con verificación, copia pre-restauración |
| **Configuración** | Taller, técnico, costos, temas (claro/oscuro), formato de orden |

## Tecnologías

<p align="center">
  <img src="https://img.shields.io/badge/PyQt6-6.5%2B-41CD52?logo=qt" alt="PyQt6 6.5+"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0%2B-ff6600?logo=database" alt="SQLAlchemy 2"/>
  <img src="https://img.shields.io/badge/Alembic-1.12%2B-557777?logo=python" alt="Alembic"/>
  <img src="https://img.shields.io/badge/Pillow-10.0%2B-3776AB?logo=python" alt="Pillow"/>
  <img src="https://img.shields.io/badge/ReportLab-4.0%2B-E4231B?logo=adobe" alt="ReportLab"/>
  <img src="https://img.shields.io/badge/matplotlib-3.7%2B-1155AA?logo=python" alt="matplotlib"/>
  <img src="https://img.shields.io/badge/platformdirs-3.0%2B-3776AB" alt="platformdirs"/>
  <img src="https://img.shields.io/badge/pytest-7.0%2B-0A9EDC?logo=pytest" alt="pytest"/>
</p>

## Instalación rápida

### Linux — inicio rápido

Después de instalar las dependencias, el comando recomendado desde la carpeta
del proyecto es:

```bash
python3 main.py
```

No necesitas configurar `PYTHONPATH`. También puedes usar el lanzador de Linux,
que configura automáticamente las variables de compatibilidad de Qt:

```bash
./run.sh
```

### Entorno virtual (recomendado)

```bash
python3 -m venv venv && source venv/bin/activate   # Linux/macOS
python -m venv venv && venv\Scripts\activate        # Windows

pip install -e .
jl-mantenimiento
```

### Linux (paquetes del sistema)

```bash
sudo apt install python3-pyqt6 python3-sqlalchemy python3-platformdirs \
    python3-pil python3-reportlab python3-matplotlib
```

### Linux (paquetes del sistema — sin venv)

Usa el lanzador incluido:

```bash
./run.sh
```

El equivalente manual, útil para diagnóstico, es:

```bash
QT_QPA_PLATFORM=xcb QT_QPA_PLATFORMTHEME= \
  QT_LOGGING_RULES='*.debug=false;qt6ct.*=false' python3 main.py
```

> **Nota:** `QT_QPA_PLATFORMTHEME=` deshabilita qt6ct, que puede causar fallos
> en algunas distribuciones. El lanzador usa X11 (`xcb`) por defecto, pero
> respeta un valor de `QT_QPA_PLATFORM` definido previamente.

### Windows (ejecutable)

```bash
pip install pyinstaller
pyinstaller packaging/jl-mantenimiento.spec
dist\JL_Mantenimiento.exe
```

### AppImage (Linux)

```bash
bash packaging/build_appimage.sh
# Luego: linuxdeploy --appdir=AppDir --output=appimage
```

## Capturas de pantalla

> Próximamente: capturas de la interfaz en funcionamiento.

## Estado del desarrollo

El avance funcional y las tareas pendientes se mantienen en
[`ROADMAP.md`](ROADMAP.md). Los agentes o colaboradores que continúen el
desarrollo deben leer también [`AGENTS.md`](AGENTS.md), que contiene la
arquitectura actual, comandos de validación, riesgos y prioridades.

## Estructura del proyecto

```
luciotech/
├── main.py                     # Lanzador directo: python3 main.py
├── src/luciotech/
│   ├── main.py                 # Punto de entrada
│   ├── app.py                  # Configuración de QApplication
│   ├── config.py               # Constantes, rutas multiplataforma
│   ├── database/
│   │   ├── connection.py       # Motor SQLite + SQLAlchemy
│   │   ├── models.py           # 8 entidades (Customer → Settings)
│   │   ├── repositories.py     # CRUD con búsqueda y filtros
│   │   └── migrations/         # Alembic para migraciones
│   ├── services/
│   │   ├── order_service.py    # CustomerService, EquipmentService, OrderService
│   │   ├── image_service.py    # Procesamiento de imágenes (Pillow)
│   │   ├── backup_service.py   # Copias de seguridad ZIP
│   │   ├── history_service.py  # Historial global unificado
│   │   └── settings_service.py # Configuración tipada y catálogos
│   ├── ui/
│   │   ├── main_window.py      # QMainWindow con sidebar colapsable
│   │   ├── pages/              # Páginas principales (órdenes, recepción, reportes)
│   │   ├── dialogs/            # Diálogos (cliente, orden, configuración)
│   │   └── widgets/            # Widgets (editor, fotos, historial, pagos)
│   ├── reports/
│   │   └── pdf_service.py      # Generador PDF (ReportLab)
│   └── utils/
│       └── logging_config.py   # Logging con rotación
├── tests/
│   └── test_core.py            # 9 pruebas unitarias
├── packaging/
│   ├── jl-mantenimiento.desktop    # Linux desktop entry
│   ├── jl-mantenimiento.appdata.xml # AppStream metadata
│   ├── build_appimage.sh       # Script AppImage
│   └── jl-mantenimiento.spec   # PyInstaller (Windows)
├── pyproject.toml
├── requirements.txt
├── README.md
├── ROADMAP.md
├── AGENTS.md
└── LICENSE
```

## Flujo de uso rápido

1. **Abrir** el programa
2. **Nueva recepción** → buscar/crear cliente → registrar equipo → guardar
3. **Lista de órdenes** → doble clic para abrir
4. **Pestaña Diagnóstico** → escribir con formato (negrita, colores, tablas)
5. **Pestaña Fotografías** → cargar fotos desde disco/carpeta (celular)
6. **Pestaña Presupuesto** → añadir conceptos, registrar pagos
7. **Botones PDF** → generar comprobante o informe técnico
8. **Configuración** → cambiar tema, datos del taller

## Ubicación de datos

| Sistema | Ruta |
|---|---|
| **Linux** | `~/.local/share/JL Mantenimiento/` |
| **Windows** | `%LOCALAPPDATA%\LucioTech\JL Mantenimiento\` |
| **macOS** | `~/Library/Application Support/JL Mantenimiento/` |

Las rutas exactas se calculan con `platformdirs`. En Linux, los logs se guardan
en `~/.local/state/JL Mantenimiento/log/`.

## Pruebas

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
```

| Prueba | Descripción |
|---|---|
| `test_create_customer` | Creación de cliente |
| `test_search_customer` | Búsqueda por texto |
| `test_duplicate_customer` | Detección por ID |
| `test_create_equipment` | Registro de equipo |
| `test_create_order` | Generación de orden |
| `test_order_number_generation` | Formato automático |
| `test_change_status` | Cambio + historial |
| `test_payment_and_balance` | Pagos + saldo |
| `test_database_persistence` | Persistencia SQLite |

## Empaquetado

| Formato | Comando |
|---|---|
| **.deb** (Debian) | `dpkg-deb --build packaging/debian` |
| **AppImage** | `bash packaging/build_appimage.sh` |
| **.exe** (Windows) | `pyinstaller packaging/jl-mantenimiento.spec` |

## Resolución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: PyQt6` | `pip install PyQt6` o usar paquetes del sistema |
| `ModuleNotFoundError: platformdirs` | `pip install platformdirs` |
| Error de base de datos | Verificar permisos en `~/.local/share/` |
| PDF no genera | `pip install reportlab` |
| Tema oscuro no aplica | Ir a Configuración → Apariencia → Oscuro (Fusion) |

## Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcion`)
3. Commit (`git commit -m "Añadida nueva función"`)
4. Push (`git push origin feature/nueva-funcion`)
5. Abre un Pull Request

## Licencia

Distribuido bajo la licencia **MIT**. Ver [`LICENSE`](LICENSE) para más detalles.

---

<p align="center">
  Hecho con ❤️ para el servicio técnico de <strong>Ing. Joseph Lucio</strong>
</p>
