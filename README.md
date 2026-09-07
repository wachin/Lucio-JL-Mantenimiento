# 🔧 JL Mantenimiento

<p align="center">
  <strong>Sistema profesional de recepción, diagnóstico, reparación, cobro y entrega de equipos informáticos y electrónicos.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white&style=for-the-badge" alt="Python 3.11+"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/UI-PyQt6-41CD52?logo=qt&logoColor=white&style=for-the-badge" alt="PyQt6"/></a>
  <a href="https://www.sqlalchemy.org/"><img src="https://img.shields.io/badge/DB-SQLAlchemy%202-d71f00?logo=sqlite&logoColor=white&style=for-the-badge" alt="SQLAlchemy 2"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/SQLite-3-003b57?logo=sqlite&logoColor=white&style=for-the-badge" alt="SQLite"/></a>
  <a href="https://github.com/Lucio-JL-Mantenimiento/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License MIT"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black&style=for-the-badge" alt="Linux"/>
  <img src="https://img.shields.io/badge/Windows-0078D6?logo=windows&logoColor=white&style=for-the-badge" alt="Windows"/>
  <img src="https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white&style=for-the-badge" alt="macOS"/>
  <img src="https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white&style=for-the-badge" alt="pytest"/>
  <img src="https://img.shields.io/badge/PDF-ReportLab-E4231B?style=for-the-badge" alt="ReportLab"/>
</p>

---

## ✨ ¿Qué es JL Mantenimiento?

**JL Mantenimiento** es una aplicación de escritorio pensada para talleres y
centros de servicio de equipos informáticos y electrónicos. Automatiza todo el
ciclo de atención al cliente: desde que el equipo **entra** al taller hasta que
se **entrega**, pasando por el diagnóstico, la reparación, la generación de
presupuestos y el cobro.

> 🎯 **Objetivo:** reemplazar los cuadernos, hojas de cálculo y papeles sueltos
> por un flujo digital, ordenado y profesional.

---

## 🚀 Características

| Módulo | Funcionalidades |
|---|---|
| **📥 Recepción** | Registro de ingreso, datos del cliente y equipo, accesorios rápidos, fotografías desde el celular |
| **📋 Órdenes** | Lista avanzada con filtros, búsqueda en tiempo real, doble clic para abrir, papelera |
| **🔍 Diagnóstico** | Editor enriquecido tipo Word (negrita, colores, tablas, imágenes, buscar/reemplazar) |
| **📸 Fotografías** | Carga, miniaturas, rotación, clasificación por tipo, vista completa |
| **🕓 Historial** | Línea de tiempo de estados y eventos, notas internas, eventos tipificados |
| **💰 Presupuesto** | Conceptos con cálculo automático, pagos, saldo pendiente, impuestos configurables |
| **📄 PDF** | Comprobante de recepción, informe técnico, vista previa, impresión directa |
| **📊 Reportes** | Filtros por fecha/estado, exportación PDF y CSV, resumen económico |
| **🗄️ Copias de seguridad** | ZIP completo (DB + fotos + config), restaurar con verificación, copia pre-restauración |
| **⚙️ Configuración** | Taller, técnico, costos, temas (claro/oscuro), formato de orden |

---

## 🧰 Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| [Python](https://www.python.org/) | 3.11+ | Lenguaje principal |
| [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) | 6.5+ | Interfaz gráfica |
| [SQLAlchemy 2](https://www.sqlalchemy.org/) | 2.0+ | ORM para base de datos |
| [SQLite](https://www.sqlite.org/) | 3 | Base de datos embebida |
| [Alembic](https://alembic.sqlalchemy.org/) | 1.12+ | Migraciones de base de datos |
| [Pillow](https://python-pillow.org/) | 10.0+ | Procesamiento de imágenes |
| [ReportLab](https://www.reportlab.com/) | 4.0+ | Generación de PDF |
| [matplotlib](https://matplotlib.org/) | 3.7+ | Gráficas y reportes |
| [platformdirs](https://github.com/platformdirs/platformdirs) | 3.0+ | Rutas de datos multiplataforma |
| [pytest](https://docs.pytest.org/) | 7.0+ | Pruebas automatizadas |

---

## 📦 Instalación

### 🐍 Entorno virtual (recomendado)

Aísla las dependencias del sistema para no generar conflictos:

```bash
# Linux/macOS
python3 -m venv venv && source venv/bin/activate

# Windows
python -m venv venv && venv\Scripts\activate
```

Una vez activo el entorno, instala el paquete en modo editable:

```bash
pip install -e .
jl-mantenimiento
```

### ▶️ Inicio rápido

```bash
# Linux/macOS
python3 main.py

# Windows
python main.py
```

### 🐧 Linux (paquetes del sistema)

```bash
sudo apt install python3-pyqt6 python3-sqlalchemy python3-platformdirs \
    python3-pil python3-reportlab python3-matplotlib
```

O usa el lanzador incluido, que configura las variables de compatibilidad de Qt:

```bash
./run.sh
```

### 🪟 Windows — Guía de desarrollo

Sección orientada a desarrolladores que quieran **instalar y ejecutar el
proyecto desde cero** en Windows 10/11. Presupone que ya tienes Python (3.11+)
instalado y añadido al `PATH`.

#### 1. Crear el entorno virtual (solo la primera vez)

Desde la carpeta del proyecto:

```bat
python -m venv venv
```

Esto crea una carpeta `venv\` aislada que contiene el intérprete y los paquetes.
Solo hay que ejecutarlo **una sola vez por proyecto**.

#### 2. Activar el entorno virtual

```bat
venv\Scripts\activate
```

Notarás que el prompt de la terminal cambia y aparece `(venv)`. Todo lo que
instales o ejecutes a partir de aquí usa el Python de `venv`.

#### 3. Instalar todas las dependencias

Con el entorno activado:

```bat
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` incluye:

| Paquete | Función |
|---|---|
| `PyQt6` | Interfaz gráfica |
| `PyQt6-tools` | Utilidades/designer de Qt (opcional, para desarrollo) |
| `SQLAlchemy` | ORM para la base de datos SQLite |
| `alembic` | Migraciones de base de datos |
| `platformdirs` | Rutas de datos multiplataforma |
| `Pillow` | Procesamiento de imágenes |
| `reportlab` | Generación de PDF |
| `matplotlib` | Gráficas y reportes |

Para poder ejecutar la **suite de pruebas** (`pytest`), instala además las
dependencias de desarrollo:

```bat
pip install pytest pytest-qt
```

> Puedes instalar todo de una vez con `pip install -r requirements.txt pytest pytest-qt`.

#### 4. Lanzar el programa

```bat
python main.py
```

#### 5. Desactivar el entorno virtual

Cuando termines de trabajar, devuelve la terminal a la normalidad:

```bat
deactivate
```

> **💡 Importante:** no hace falta crear el `venv` de nuevo en cada sesión. Una
> vez creado e instaladas las dependencias, para lanzar el programa solo tienes
> que activar el entorno y ejecutar `python main.py`:

```bat
cd C:\D\Lucio-JL-Mantenimiento
venv\Scripts\activate
python main.py
```

Si prefieres no activar el entorno manualmente, puedes usar el lanzador incluido
(`iniciar.bat`), que activa el entorno y arranca la aplicación con doble clic.

#### Ejecutar las pruebas

Con el entorno activado:

```bat
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTHONPATH="src"
python -m pytest -q
```

### 📦 Empaquetado

| Formato | Comando |
|---|---|
| **.deb** (Debian) | `dpkg-deb --build packaging/debian` |
| **AppImage** | `bash packaging/build_appimage.sh` |
| **.exe** (Windows) | `pyinstaller packaging/jl-mantenimiento.spec` |

---

## 🧪 Pruebas

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

---

## 🗂️ Estructura del proyecto

```
luciotech/
├── main.py                     # Lanzador directo: python main.py
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
│   └── test_core.py            # Pruebas unitarias
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

---

## 🎬 Flujo de uso rápido

1. **Abrir** el programa
2. **Nueva recepción** → buscar/crear cliente → registrar equipo → guardar
3. **Lista de órdenes** → doble clic para abrir
4. **Pestaña Diagnóstico** → escribir con formato (negrita, colores, tablas)
5. **Pestaña Fotografías** → cargar fotos desde disco/carpeta (celular)
6. **Pestaña Presupuesto** → añadir conceptos, registrar pagos
7. **Botones PDF** → generar comprobante o informe técnico
8. **Configuración** → cambiar tema, datos del taller

---

## 📁 Ubicación de datos

| Sistema | Ruta |
|---|---|
| **Linux** | `~/.local/share/JL Mantenimiento/` |
| **Windows** | `%LOCALAPPDATA%\LucioTech\JL Mantenimiento\` |
| **macOS** | `~/Library/Application Support/JL Mantenimiento/` |

Las rutas exactas se calculan con `platformdirs`. En Linux, los logs se guardan
en `~/.local/state/JL Mantenimiento/log/`.

---

## 🛠️ Resolución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: PyQt6` | `pip install PyQt6` o usar paquetes del sistema |
| `ModuleNotFoundError: platformdirs` | `pip install platformdirs` |
| Error de base de datos | Verificar permisos en `~/.local/share/` |
| PDF no genera | `pip install reportlab` |
| Tema oscuro no aplica | Ir a Configuración → Apariencia → Oscuro (Fusion) |

---

## 🤝 Contribuir

1. Haz un **fork** del repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcion`)
3. Realiza tus cambios y **commit** (`git commit -m "Añadida nueva función"`)
4. **Push** (`git push origin feature/nueva-funcion`)
5. Abre un **Pull Request**

> Para saber cómo evoluciona el proyecto y qué tareas están pendientes, lee
> [`ROADMAP.md`](ROADMAP.md). Los colaboradores deben revisar también
> [`AGENTS.md`](AGENTS.md), que documenta la arquitectura y las reglas del código.

---

## 📄 Licencia

Distribuido bajo la licencia **MIT**. Ver [`LICENSE`](LICENSE) para más detalles.

---

<p align="center">
  <strong>Dios te bendiga <a href="https://github.com/Lucio-JL-Mantenimiento">Ing. Joseph Lucio</a> ⭐</strong>
</p>