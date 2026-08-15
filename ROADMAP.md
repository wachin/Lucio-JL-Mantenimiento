# Roadmap de JL Mantenimiento

Estado verificado el **2026-08-15** contra el código del repositorio. Última actualización: iteración P0 (backups seguros, presupuestos persistentes, ampliación de pruebas).

Leyenda:

- [x] Implementado y disponible en el código actual.
- [ ] Pendiente, incompleto o todavía sin validación suficiente.

Una tarea parcialmente implementada se divide en subtareas marcadas y
desmarcadas. No se considera terminada solo porque exista una pantalla o clase.

## 1. Base del proyecto

- [x] Nombre de la aplicación: JL Mantenimiento.
- [x] Python 3.11 o superior.
- [x] Interfaz de escritorio con PyQt6.
- [x] Persistencia local con SQLite y SQLAlchemy 2.
- [x] Rutas de datos y logs mediante `platformdirs`.
- [x] Arquitectura separada en base de datos, servicios, UI, reportes y utilidades.
- [x] Punto de entrada directo `python3 main.py`.
- [x] Lanzador Linux `./run.sh`.
- [x] Entrada instalable `jl-mantenimiento` definida en `pyproject.toml`.
- [x] Funcionamiento sin conexión a internet.
- [ ] Configuración completa y operativa de Alembic con revisiones versionadas.
- [ ] Internacionalización real mediante catálogos de traducción.

## 2. Base de datos

- [x] Modelo de clientes.
- [x] Modelo de equipos asociados a clientes.
- [x] Modelo de órdenes de servicio.
- [x] Modelo de fotografías.
- [x] Modelo de cambios de estado.
- [x] Modelo de eventos del historial.
- [x] Modelo de pagos.
- [x] Modelo clave/valor para configuración.
- [x] Creación automática de tablas al iniciar.
- [x] Claves foráneas activadas en SQLite.
- [x] Eliminación lógica de clientes y órdenes.
- [x] Papelera y restauración de órdenes.
- [x] Reinicio controlado de la conexión para pruebas aisladas.
- [ ] Migraciones Alembic reproducibles para actualizar instalaciones existentes.
- [ ] Política de cierre explícito de sesiones de larga duración en widgets.
- [ ] Índices y medición de rendimiento con bases de datos grandes.

## 3. Ventana principal y navegación

- [x] Ventana principal redimensionable con tamaño mínimo 1200 × 700.
- [x] Barra lateral con Inicio, Órdenes, Recepción, Clientes, Equipos, Historial,
  Reportes, Backups y Configuración.
- [x] Navegación mediante `QStackedWidget`.
- [x] Atajo `Ctrl+N` para nueva recepción.
- [x] Atajo `Ctrl+F` para buscar órdenes.
- [x] Barra de estado.
- [x] Persistencia de la referencia Python de la ventana principal.
- [ ] Conectar la acción global `Ctrl+P` a una impresión contextual válida.
- [ ] Iconos definitivos y sistema visual consistente.
- [ ] Recordar tamaño, posición, divisores y sección abierta.
- [ ] Barra lateral realmente colapsable desde la interfaz.

## 4. Panel de inicio

- [x] Contador de órdenes activas.
- [x] Contador de órdenes listas para entregar.
- [x] Contador de órdenes retrasadas.
- [x] Saldo total pendiente.
- [x] Resumen por estado.
- [x] Diez órdenes recientes con apertura por doble clic.
- [x] Accesos a nueva recepción y lista de órdenes.
- [x] Actualización al volver a Inicio.
- [ ] Equipos recibidos hoy como indicador independiente.
- [ ] Equipos entregados durante el mes.
- [ ] Ingresos reales del mes basados en pagos, no en totales presupuestados.
- [ ] Entregas estimadas próximas.
- [ ] Gráficos opcionales.

## 5. Clientes

- [x] Crear clientes desde diálogo y desde Recepción.
- [x] Editar clientes existentes.
- [x] Buscar por nombre, identificación, teléfono o correo.
- [x] Tabla general de clientes.
- [x] Validar nombre y teléfono obligatorios.
- [x] Evitar identificaciones duplicadas.
- [x] Mostrar cantidad de equipos asociados.
- [x] Integración segura entre sesiones SQLAlchemy de páginas y diálogos.
- [ ] Validar formato de teléfono y correo.
- [ ] Advertir posibles duplicados por teléfono, además de identificación.
- [ ] Ficha completa con equipos, órdenes, pagos, saldos y última visita.
- [ ] Mostrar órdenes anteriores dentro de Nueva recepción.
- [ ] Papelera y restauración de clientes desde la UI.

## 6. Equipos

- [x] Registrar equipos durante una recepción.
- [x] Inventario buscable por propietario, tipo, marca, modelo, serie y problema.
- [x] Editar la ficha técnica de un equipo.
- [x] Ocultar y mostrar contraseña/PIN en la edición.
- [x] Evitar números de serie duplicados.
- [x] Tipos de equipo configurables.
- [x] Accesorios sugeridos para los tipos principales.
- [ ] Advertencia no bloqueante para series duplicadas cuando sea legítimo repetirlas.
- [ ] Historial completo del equipo y sus órdenes desde la ficha.
- [ ] Cifrado en reposo de contraseñas/PIN o decisión documentada sobre su alcance.

## 7. Nueva recepción

- [x] Seleccionar o crear cliente sin abandonar el formulario.
- [x] Editar datos básicos del cliente seleccionado.
- [x] Capturar tipo, marca, modelo, serie, color y sistema operativo.
- [x] Capturar contraseña/PIN como campo oculto.
- [x] Capturar accesorios, estado físico, problema y observaciones.
- [x] Capturar fecha/hora de ingreso y fecha estimada.
- [x] Capturar prioridad, técnico, costo de diagnóstico, anticipo y estado inicial.
- [x] Usar técnico y garantía predeterminados desde Configuración.
- [x] Crear cliente, equipo, orden, pago inicial e historial.
- [ ] Validar que la fecha estimada no sea anterior al ingreso.
- [ ] Validar que el anticipo no supere el total o manejar crédito explícitamente.
- [ ] Importar fotografías durante la recepción, antes de guardar la orden.
- [ ] Pantalla de confirmación previa con resumen y número que se generará.
- [ ] Variantes de campos/accesorios más completas por tipo de equipo.
- [ ] Transacción atómica: revertir cliente/equipo si falla la creación final.

## 8. Órdenes de servicio

- [x] Generación automática de número de orden.
- [x] Formato de número configurable y validado.
- [x] Secuencia diaria sin colisiones, incluyendo órdenes en papelera.
- [x] Lista con cliente, equipo, problema, estado, prioridad, total y saldo.
- [x] Búsqueda por texto.
- [x] Filtros por estado, prioridad, saldo, retraso y fechas.
- [x] Ordenamiento por columnas.
- [x] Apertura por doble clic y menú contextual.
- [x] Papelera visible, buscable y restaurable.
- [x] Asociación correcta de filas después de ordenar la tabla.
- [ ] Elegir columnas visibles y guardar anchos/orden.
- [ ] Selección múltiple y acciones por lote.
- [ ] Exportar o imprimir directamente el listado filtrado.
- [ ] Eliminación definitiva controlada desde la papelera.

## 9. Vista y edición de una orden

- [x] Resumen de orden, cliente y equipo.
- [x] Cambio de estado con registro automático en historial.
- [x] Pestañas de diagnóstico, historial, fotografías y presupuesto/pagos.
- [x] Corrección de la creación diferida del widget de historial.
- [x] Generación de comprobante e informe técnico.
- [x] Impresión mediante diálogo del sistema.
- [ ] Editar todos los datos generales de la orden desde su ficha.
- [ ] Registrar fecha de finalización y entrega automáticamente según estado.
- [ ] Mostrar/ocultar contraseña/PIN en la ficha de orden.
- [ ] Refrescar todas las pestañas sin reconstruir widgets y sesiones repetidamente.

## 10. Editor enriquecido

- [x] Fuente y tamaño.
- [x] Negrita, cursiva, subrayado y tachado.
- [x] Color de texto y fondo.
- [x] Alineación izquierda, centro, derecha y justificada.
- [x] Listas con viñetas y numeradas.
- [x] Sangría básica.
- [x] Deshacer, rehacer, cortar, copiar y pegar.
- [x] Pegado como texto plano.
- [x] Insertar tabla, imagen y línea horizontal.
- [x] Buscar y reemplazar.
- [x] Limpiar formato.
- [x] Vista previa de impresión.
- [x] Guardar diagnóstico, trabajo realizado y recomendaciones como HTML.
- [ ] Zoom del editor.
- [ ] Edición avanzada de tablas.
- [ ] Copiar imágenes insertadas al directorio de datos; hoy pueden depender de
  su ruta original.
- [ ] Fidelidad completa de texto enriquecido, tablas e imágenes al exportar PDF.

## 11. Historial

- [x] Crear registro al crear una orden.
- [x] Crear registro al cambiar de estado.
- [x] Añadir eventos tipificados y notas internas.
- [x] Línea de tiempo dentro de la orden.
- [x] Historial global combinado y ordenado cronológicamente.
- [x] Buscar por orden, cliente, equipo, estado, evento, detalle o usuario.
- [x] Filtrar por cambios de estado, eventos o tipo de evento.
- [x] Abrir la orden desde el historial global.
- [ ] Auditoría detallada de cambios de campos, no solo estados y eventos manuales.
- [ ] Edición/eliminación controlada de eventos incorrectos.

## 12. Fotografías

- [x] Selección múltiple desde archivos.
- [x] Importación de todas las imágenes de una carpeta.
- [x] Copia al directorio de datos con nombre UUID.
- [x] Validación básica por extensión.
- [x] Corrección de orientación EXIF.
- [x] Redimensionamiento de imágenes grandes.
- [x] Generación de miniaturas.
- [x] Vista en miniaturas y vista ampliada.
- [x] Clasificación y edición de descripción.
- [x] Rotación.
- [x] Eliminación con confirmación y borrado de archivos.
- [x] Inclusión de fotografías en PDF.
- [ ] Arrastrar y soltar imágenes.
- [ ] Pegar desde el portapapeles.
- [ ] Reordenar fotografías desde la interfaz (el repositorio ya lo permite).
- [ ] Importación directa mediante MTP/GVFS y documentación del flujo desde celular.
- [ ] Validar contenido MIME además de extensión.
- [ ] Reportar individualmente archivos rechazados; hoy solo se registran en logs.

## 13. Presupuestos, costos y pagos

- [x] Tabla editable de conceptos con tipo, descripción, cantidad y precio.
- [x] Cálculo visual de subtotales y total.
- [x] Guardar total y saldo en la orden.
- [x] Registrar pagos con tipo, método, monto, referencia y notas.
- [x] Recalcular saldo a partir de pagos.
- [x] Registrar eventos por pagos.
- [x] Corregir saldo inicial cuando no existe anticipo.
- [x] Modelo persistente para conceptos del presupuesto (`BudgetConcept` con tipo,
  descripción, cantidad, precio unitario y subtotales). Los conceptos se cargan
  al reabrir la orden y se guardan con el presupuesto.
- [ ] Controles editables y cálculo real de descuento e impuestos.
- [ ] Aplicar moneda configurada en toda la UI, no solo documentos.
- [ ] Validar sobrepagos, reembolsos y montos negativos según tipo.
- [ ] Editar o anular pagos con trazabilidad.
- [ ] Estado de aprobación/rechazo del presupuesto.

## 14. PDF e impresión

- [x] Comprobante de recepción A4.
- [x] Informe técnico A4.
- [x] Datos configurados del taller, técnico, contacto, moneda y logo.
- [x] Datos de orden, cliente, equipo, costos, garantía, fotos y firmas.
- [x] Nombres de archivo seguros y directorio de reportes.
- [x] Escape de caracteres especiales en datos ingresados por usuarios.
- [x] Impresión de resumen mediante `QPrintDialog`.
- [x] Vista previa desde el editor enriquecido.
- [ ] PDF de presupuesto.
- [ ] Comprobante de entrega.
- [ ] PDF del historial completo.
- [ ] Condiciones del servicio configurables en comprobante.
- [ ] Tamaño Carta y formato móvil 63 × 110 mm.
- [ ] Numeración de páginas, encabezado y pie repetidos.
- [ ] Márgenes configurables.
- [ ] Vista previa específica para cada documento antes de guardarlo.
- [ ] Preservar tablas, imágenes y formato enriquecido en el informe técnico.
- [ ] Pruebas automatizadas de contenido PDF.

## 15. Reportes

- [x] Filtros por rango de fechas y estado.
- [x] Tabla de resultados de órdenes.
- [x] Conteo por estado.
- [x] Resumen de totales y saldos.
- [x] Exportación CSV.
- [x] Exportación PDF tabular.
- [ ] Calcular ingresos desde pagos recibidos en el periodo.
- [ ] Filtros por técnico, prioridad, cliente, tipo y marca.
- [ ] Reportes de tiempos promedio, garantías y equipos frecuentes.
- [ ] Gráficos.
- [ ] Aplicar moneda y encabezado configurados a los reportes exportados.
- [ ] Impresión directa de reportes.

## 16. Copias de seguridad

- [x] Formato `.jlmb` basado en ZIP.
- [x] Copia manual de base de datos y fotografías.
- [x] Metadatos con fecha, versión y cantidad de archivos.
- [x] Elección de carpeta de destino.
- [x] Verificación de integridad SQLite antes de copiar y después de restaurar.
- [x] Lista básica de backups presentes en el directorio predeterminado.
- [x] Confirmación antes de restaurar.
- [x] Usar la API de backup de SQLite (`Connection.backup()`) para obtener una copia
  consistente mientras la aplicación está abierta.
- [x] Crear copia pre-restauración automática en el directorio de backups.
- [x] Validar rutas del ZIP y evitar extracción fuera del directorio de datos
  (protección contra Zip Slip).
- [x] Restauración transaccional: extrae a directorio temporal, verifica integridad
  y solo entonces reemplaza los datos actuales.
- [ ] Copias automáticas y retención de las últimas N.
- [ ] Incluir logo externo, plantillas y otros archivos configurados.
- [ ] Botón para abrir la carpeta de backups.
- [x] Pruebas automatizadas de creación y restauración (Zip Slip, backup consistente, restore atómico).

## 17. Configuración

- [x] Datos del taller y logo.
- [x] Datos del técnico.
- [x] Formato configurable de número de orden.
- [x] Garantía predeterminada.
- [x] Moneda e impuestos almacenados.
- [x] Temas sistema, Fusion claro y Fusion oscuro.
- [x] Carga del tema guardado al iniciar.
- [x] Catálogo administrable de tipos de equipo.
- [x] Aplicación inmediata del catálogo en Nueva recepción.
- [x] Restablecimiento general de configuración.
- [ ] Aplicar tasa de impuestos automáticamente al presupuesto.
- [ ] Catálogos administrables de estados, prioridades, accesorios, eventos,
  métodos y tipos de pago.
- [ ] Plantillas de texto, condiciones de servicio y notas frecuentes.
- [ ] Configuración de rutas de reportes, backups y adjuntos.
- [ ] Tamaño de fuente de la interfaz.
- [ ] Validaciones de teléfono, correo e identificación configurables.

## 18. Diseño, accesibilidad y usabilidad

- [x] Uso general de paleta Qt y soporte claro/oscuro.
- [x] Campos obligatorios indicados en los formularios principales.
- [x] Mensajes comprensibles y confirmaciones para borrados.
- [x] Atajos básicos y doble clic en tablas.
- [x] Contraseña/PIN oculto por defecto en formularios editables.
- [ ] Revisión completa de contraste; aún existen colores fijos en algunos widgets.
- [ ] Navegación integral solo con teclado y orden de tabulación revisado.
- [ ] Nombres accesibles y ayudas para lector de pantalla.
- [ ] Tamaño de fuente configurable.
- [ ] Tooltips consistentes para todas las acciones.
- [ ] Pruebas en resoluciones menores y escalado HiDPI.

## 19. Seguridad, privacidad y robustez

- [x] Sin servicios externos ni telemetría.
- [x] Consultas ORM parametrizadas con SQLAlchemy.
- [x] Contraseñas/PIN no incluidos deliberadamente en logs.
- [x] Campos sensibles ocultos por defecto.
- [x] Escape de datos de usuario en PDF e impresión HTML.
- [x] UUID para impedir colisiones entre fotografías importadas.
- [x] Confirmación antes de eliminar órdenes, fotos y restaurar backups.
- [ ] Cifrado o política explícita para contraseñas almacenadas en SQLite.
- [x] Validación segura contra Zip Slip al restaurar backups (`_validate_zip_paths`).
- [ ] Capturador global de excepciones con diálogo y registro.
- [ ] Manejo amable cuando el directorio de logs/datos no es escribible.
- [ ] Validación MIME y límites contra imágenes maliciosas o enormes.

## 20. Logging y diagnóstico

- [x] Archivo rotativo de 5 MB con tres respaldos.
- [x] Registro de inicio, conexión, ventanas, órdenes, imágenes, PDF y backups.
- [x] Consola limitada a advertencias y errores.
- [ ] Registrar cierre normal de la aplicación.
- [ ] Capturar excepciones no controladas de Python y Qt.
- [ ] Evitar handlers duplicados si se crea la aplicación más de una vez en pruebas.
- [ ] Pantalla para abrir/copiar logs desde Configuración.

## 21. Pruebas y calidad

- [x] Suite con 27 pruebas: clientes, equipos, órdenes, estados, pagos, saldo,
  persistencia, backups seguros (Zip Slip, backup consistente, restauración
  atómica), presupuestos persistentes, papelera e historial global.
- [x] Aislamiento de la base SQLite entre pruebas.
- [x] Ejecución actual: `27 passed` con `PYTHONPATH=src pytest -q`.
- [x] `.gitignore` para cachés, entornos, builds y logs.
- [ ] Pruebas de validaciones de duplicados y formatos configurables.
- [x] Pruebas de papelera, restauración e historial global (cubiertas en `test_p0_features.py`).
- [ ] Pruebas de repositorios restantes (equipos, fotos, configuración).
- [ ] Pruebas UI con `pytest-qt`.
- [ ] Pruebas del editor enriquecido.
- [ ] Pruebas de importación, rotación y borrado de fotografías.
- [ ] Pruebas de PDF e impresión HTML.
- [ ] Pruebas de backups y restauración segura.
- [ ] Pruebas de migraciones.
- [ ] Linter, formateador y comprobación de tipos configurados en CI.
- [ ] Integración continua en GitHub Actions u otro sistema.

## 22. Empaquetado y plataformas

- [x] Metadatos de proyecto y dependencias en `pyproject.toml`.
- [x] Archivo `.desktop` y metadatos AppStream iniciales.
- [x] Especificación inicial de PyInstaller para Windows.
- [x] Script inicial para estructura AppDir/AppImage.
- [x] Rutas de datos multiplataforma mediante `platformdirs`.
- [x] Apertura externa de PDF diferenciada por Linux, Windows y macOS.
- [x] Eliminar archivos `__pycache__` rastreados por Git y evitar que regresen.
- [ ] Corregir y probar el AppImage; el script actual es solo un esqueleto y su
  distribución de `src`/`PYTHONPATH` debe verificarse.
- [ ] Actualizar hidden imports de PyInstaller con las páginas y servicios nuevos.
- [ ] Iconos reales en tamaños requeridos.
- [ ] Paquete `.deb`.
- [ ] Instalador o ejecutable Windows validado sin Python instalado.
- [ ] Pruebas manuales en Debian, Ubuntu, MX Linux, Windows y macOS.
- [ ] Registrar opcionalmente la extensión `.jlmb`.

## 23. Documentación

- [x] README con descripción, características, instalación, ejecución, estructura,
  datos, pruebas, empaquetado y resolución de problemas.
- [x] Comando directo `python3 main.py` documentado.
- [x] Roadmap transformado en checklist verificable.
- [x] Guía `AGENTS.md` para continuidad del desarrollo.
- [ ] Capturas de pantalla reales.
- [ ] Manual de usuario con flujo completo.
- [ ] Documentar creación y restauración de backups paso a paso.
- [ ] Documentación de arquitectura y decisiones técnicas de largo plazo.
- [x] Alinear las rutas de datos mostradas en README con `platformdirs` y los
  valores actuales de `APP_NAME`/`ORG_NAME`.

## 24. Prioridad recomendada para las próximas iteraciones

- [x] **P0 — Seguridad de backups:** validar miembros ZIP (Zip Slip), backup
  consistente con `sqlite3.Connection.backup()`, restauración transaccional con
  extracción a directorio temporal y copia pre-restauración automática.
- [x] **P0 — Presupuestos persistentes:** modelo `BudgetConcept` con repositorio,
  carga y guardado de conceptos desde la pestaña de presupuesto. Impuestos y
  descuentos se aplican en el recálculo.
- [x] **P0 — Ampliar pruebas:** 18 pruebas nuevas que cubren backups seguros,
  presupuestos persistentes, papelera/restauración e historial global.
- [ ] **P1 — Recepción completa:** fotos antes de guardar, validaciones y resumen.
- [ ] **P1 — Ficha de cliente:** órdenes, equipos, pagos, saldos y visitas.
- [ ] **P1 — Documentos faltantes:** presupuesto y comprobante de entrega.
- [ ] **P1 — Migraciones:** convertir el esquema actual en revisiones Alembic.
- [ ] **P2 — Empaquetado real:** limpiar artefactos, completar AppImage/PyInstaller
  y probar plataformas objetivo.
- [ ] **P2 — Accesibilidad, traducciones y persistencia de preferencias visuales.**

## 25. Criterio para marcar tareas futuras

- [x] Marcar una tarea solo cuando el flujo esté conectado a la UI o API usada.
- [x] Exigir una prueba automatizada o una validación reproducible proporcional al
  riesgo antes de pasar de `[ ]` a `[x]`.
- [x] Si una función es parcial, dividirla; no marcar el bloque completo.
- [x] Actualizar este archivo y `AGENTS.md` al cerrar cada iteración importante.
