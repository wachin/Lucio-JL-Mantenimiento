# Guía para agentes de desarrollo

## Objetivo

Continuar **JL Mantenimiento**, una aplicación de escritorio PyQt6 para el ciclo
de recepción, diagnóstico, reparación, cobro y entrega de equipos. El estado
funcional y las tareas pendientes están en `ROADMAP.md`; debe ser la fuente de
verdad y actualizarse junto con cada cambio relevante.

## Inicio rápido

```bash
python3 main.py
```

Alternativa Linux con variables de compatibilidad Qt:

```bash
./run.sh
```

Pruebas:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
```

Prueba de arranque sin una pantalla física:

```bash
tmpdir=$(mktemp -d /tmp/luciotech-smoke-XXXXXX)
XDG_DATA_HOME="$tmpdir/data" XDG_STATE_HOME="$tmpdir/state" \
XDG_CACHE_HOME="$tmpdir/cache" PYTHONDONTWRITEBYTECODE=1 \
QT_QPA_PLATFORM=offscreen timeout 3s python3 main.py
```

El código esperado del último comando es `124`: significa que la aplicación se
mantuvo abierta hasta que `timeout` la detuvo.

## Arquitectura actual

- `main.py`: lanzador directo desde la raíz.
- `src/luciotech/app.py`: creación de `QApplication`, directorios, tema y ventana.
- `src/luciotech/database/`: conexión singleton, modelos y repositorios.
- `src/luciotech/services/`: reglas de negocio, imágenes, configuración, historial
  y backups.
- `src/luciotech/ui/pages/`: pantallas principales.
- `src/luciotech/ui/dialogs/`: edición de clientes, equipos, órdenes y ajustes.
- `src/luciotech/ui/widgets/`: editor, fotos, historial y presupuesto/pagos.
- `src/luciotech/reports/pdf_service.py`: PDFs e infraestructura tabular.
- `packaging/`: artefactos iniciales; todavía no representan paquetes validados.

## Reglas importantes del código existente

1. La conexión usa un motor y fábrica de sesiones globales. En pruebas que
   cambien la ruta SQLite, llamar `reset_connection()` antes y después.
2. No conservar objetos ORM de una sesión para guardarlos directamente con otra.
   Los repositorios de clientes/equipos usan `merge`; seguir el mismo patrón.
3. Las tablas ordenables deben guardar el objeto o ID en `Qt.UserRole`. Nunca
   indexar una lista paralela por el número de fila después de ordenar.
4. Mantener una referencia fuerte a ventanas Qt de nivel superior. El arreglo de
   ciclo de vida está en `app.main_window`.
5. Usar `platformdirs`; no escribir datos de usuario dentro del repositorio.
6. No registrar contraseñas/PIN ni incorporar valores de usuario como HTML sin
   escaparlos.
7. Evitar generar bytecode durante validaciones (`PYTHONDONTWRITEBYTECODE=1`).
8. No marcar elementos del roadmap como completos si solo existe un esqueleto.

## Estado de verificación

- Suite al preparar este handoff: **9 passed**.
- Arranque offscreen validado en iteraciones recientes.
- Los `__pycache__` históricos fueron retirados del índice y `.gitignore` evita
  que vuelvan a incorporarse.
- No hay CI configurada.
- Alembic tiene estructura mínima, pero no revisiones de migración utilizables.

## Riesgos y deuda prioritaria

1. `BackupService.restore_backup()` usa extracción ZIP directa. Validar cada ruta
   antes de extraer para impedir Zip Slip y diseñar rollback.
2. Los conceptos del presupuesto viven solo en la tabla UI; al reabrir se pierde
   el detalle aunque el total sí persiste.
3. La suite base no cubre las páginas, PDF, imágenes, papelera, configuración ni
   backups añadidos posteriormente.
4. El AppImage y PyInstaller son esqueletos desactualizados respecto a módulos
   nuevos.
5. Varias pantallas mantienen sesiones SQLAlchemy durante toda su vida; vigilar
   datos obsoletos y liberar recursos.

## Flujo recomendado para cada cambio

1. Elegir una tarea desmarcada del bloque de prioridades de `ROADMAP.md`.
2. Inspeccionar el flujo completo UI → servicio → repositorio → modelo.
3. Implementar una unidad pequeña y mantener la aplicación ejecutable.
4. Añadir o actualizar pruebas; usar directorios XDG temporales para no tocar los
   datos reales del usuario.
5. Ejecutar la suite y una prueba de arranque offscreen cuando cambie la UI.
6. Actualizar las casillas del roadmap y este documento si cambia la arquitectura.

## Definition of Done

- El flujo está conectado y no es código muerto.
- Los errores previsibles se muestran de forma comprensible.
- Los datos persisten y se refrescan entre sesiones cuando corresponde.
- Hay validación automatizada o un smoke test reproducible.
- `git diff --check` no informa errores.
- `ROADMAP.md` refleja honestamente el nuevo estado.
