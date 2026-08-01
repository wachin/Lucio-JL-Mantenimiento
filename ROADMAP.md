# Prompt para Codex: Sistema de recepción y reparación de equipos en PyQt6

Quiero que desarrolles una aplicación de escritorio profesional en
**Python 3 y PyQt6** para registrar el ingreso, diagnóstico, reparación
y entrega de equipos tecnológicos recibidos por un técnico.

El programa será utilizado por:

**Ing. Joseph Lucio --- Servicio técnico de equipos informáticos y electrónicos**

La aplicación debe funcionar en **Debian, Ubuntu, MX
Linux y distribuciones derivadas**, su código debe estar preparado
para poder ejecutarse también en Windows y macOS

El programa debe ser moderno, estable, fácil de usar y apto para una persona que no tiene conocimientos avanzados de informática.

------------------------------------------------------------------------

# 1. Nombre del programa

Usar como nombre:

    JL Mantenimiento


------------------------------------------------------------------------

# 2. Objetivo del programa

El programa debe permitir registrar el ingreso de equipos al taller,
almacenar los datos del cliente y del equipo, documentar el diagnóstico
y las reparaciones realizadas, adjuntar fotografías, consultar el
historial completo e imprimir comprobantes y reportes en PDF.

Debe manejar los siguientes tipos de equipos:

- Laptop
- Computadora de escritorio
- Impresora
- Cámara de seguridad
- DVR
- NVR
- Monitor
- Router
- Fuente de alimentación
- Otro

La lista de tipos de equipos debe poder administrarse desde la
configuración del programa.

------------------------------------------------------------------------

# 3. Tecnologías obligatorias

Usar:

    Python 3.11 o superior
    PyQt6
    SQLite
    SQLAlchemy 2
    Alembic
    PyMuPDF o ReportLab para generar PDF
    Pillow para procesar imágenes
    pytest para pruebas

Para el editor enriquecido utilizar:

    QTextEdit
    QTextDocument
    QTextCursor
    QTextCharFormat
    QTextBlockFormat

No utilizar servicios externos ni requerir conexión a internet.

------------------------------------------------------------------------

# 4. Arquitectura del proyecto

Crear una estructura modular y mantenible semejante a esta:

    luciotech_service_manager/
    ├── pyproject.toml
    ├── README.md
    ├── LICENSE
    ├── requirements.txt
    ├── src/
    │   └── luciotech/
    │       ├── __init__.py
    │       ├── main.py
    │       ├── app.py
    │       ├── config.py
    │       ├── database/
    │       │   ├── connection.py
    │       │   ├── models.py
    │       │   ├── repositories.py
    │       │   └── migrations/
    │       ├── services/
    │       │   ├── customer_service.py
    │       │   ├── equipment_service.py
    │       │   ├── repair_service.py
    │       │   ├── image_service.py
    │       │   ├── pdf_service.py
    │       │   ├── backup_service.py
    │       │   └── settings_service.py
    │       ├── ui/
    │       │   ├── main_window.py
    │       │   ├── dialogs/
    │       │   ├── widgets/
    │       │   ├── pages/
    │       │   └── resources/
    │       ├── reports/
    │       │   ├── templates/
    │       │   └── styles/
    │       ├── utils/
    │       │   ├── validators.py
    │       │   ├── paths.py
    │       │   ├── dates.py
    │       │   └── logging_config.py
    │       └── translations/
    ├── tests/
    ├── packaging/
    │   ├── debian/
    │   └── appimage/
    └── docs/

Separar correctamente:

- Interfaz gráfica
- Acceso a datos
- Lógica de negocio
- Generación de documentos
- Gestión de imágenes
- Configuración
- Copias de seguridad

No colocar toda la aplicación en un único archivo.

------------------------------------------------------------------------

# 5. Base de datos

Usar SQLite mediante SQLAlchemy.

La base de datos debe guardarse por defecto en:

    ~/.local/share/lucio-jl-service-manager/database.sqlite3

En Windows debe utilizarse una ruta apropiada dentro de los datos de
aplicación del usuario.

Crear al menos las siguientes entidades.

## 5.1. Clientes

Campos:

    id
    nombre_completo
    numero_identificacion
    telefono_principal
    telefono_secundario
    correo_electronico
    direccion
    notas
    fecha_creacion
    fecha_actualizacion

El número de identificación puede ser cédula, RUC, pasaporte u otro.

## 5.2. Equipos

Campos:

    id
    cliente_id
    tipo_equipo
    marca
    modelo
    numero_serie
    color
    sistema_operativo
    contrasena_equipo
    accesorios_recibidos
    estado_fisico
    problema_reportado_cliente
    observaciones_ingreso
    fecha_creacion
    fecha_actualizacion

La contraseña del equipo debe ser opcional.

No debe mostrarse directamente en las listas generales. Añadir un botón
para mostrarla u ocultarla cuando el usuario tenga abierta la ficha.

## 5.3. Órdenes de servicio

Campos:

    id
    numero_orden
    cliente_id
    equipo_id
    fecha_ingreso
    fecha_estimada_entrega
    fecha_finalizacion
    fecha_entrega
    estado
    prioridad
    tecnico_responsable
    problema_reportado
    diagnostico_html
    trabajo_realizado_html
    recomendaciones_html
    repuestos_utilizados
    costo_diagnostico
    costo_repuestos
    costo_mano_obra
    descuento
    impuestos
    total
    anticipo
    saldo_pendiente
    garantia_dias
    notas_internas
    fecha_creacion
    fecha_actualizacion

El número de orden debe generarse automáticamente.

Usar un formato configurable

Estados disponibles:

    Recibido
    Pendiente de diagnóstico
    Diagnosticado
    Esperando aprobación
    Esperando repuesto
    En reparación
    Reparado
    Listo para entregar
    Entregado
    No reparable
    Cancelado

Prioridades:

    Baja
    Normal
    Alta
    Urgente

## 5.4. Fotografías

Campos:

    id
    orden_id
    ruta_archivo
    nombre_archivo
    descripcion
    tipo_fotografia
    fecha_captura
    fecha_creacion
    orden_visualizacion

Tipos de fotografía:

    Estado al recibir
    Número de serie
    Accesorios
    Daño físico
    Proceso de reparación
    Equipo reparado
    Otro

## 5.5. Historial de estados

Campos:

    id
    orden_id
    estado_anterior
    estado_nuevo
    comentario
    fecha
    usuario

Cada vez que cambie el estado de una orden debe crearse automáticamente
un registro en el historial.

## 5.6. Eventos o notas del historial

Campos:

    id
    orden_id
    tipo_evento
    titulo
    descripcion
    fecha
    usuario

Ejemplos de eventos:

    Llamada al cliente
    Mensaje enviado
    Presupuesto aprobado
    Presupuesto rechazado
    Repuesto solicitado
    Repuesto recibido
    Diagnóstico actualizado
    Pago recibido
    Equipo entregado
    Nota interna

## 5.7. Pagos

Campos:

    id
    orden_id
    fecha
    tipo_pago
    metodo_pago
    monto
    referencia
    observaciones

Tipos de pago:

    Anticipo
    Abono
    Pago final
    Reembolso

Métodos:

    Efectivo
    Transferencia bancaria
    Tarjeta
    Depósito
    Otro

## 5.8. Configuración

Guardar:

    nombre_taller
    nombre_tecnico
    numero_identificacion
    telefono
    correo
    direccion
    logo
    moneda
    formato_numero_orden
    texto_pie_reporte
    condiciones_servicio
    ruta_copias_seguridad
    tema_visual
    idioma

Usar como moneda predeterminada:

    USD

------------------------------------------------------------------------

# 6. Ventana principal

Crear una interfaz moderna utilizando:

    QMainWindow
    QStackedWidget
    QToolBar
    QStatusBar
    QSplitter

La ventana principal debe tener una barra lateral con estas secciones:

    Inicio
    Órdenes de servicio
    Nueva recepción
    Clientes
    Equipos
    Historial
    Reportes
    Copias de seguridad
    Configuración

La barra lateral debe poder contraerse para mostrar solamente los
iconos.

Agregar iconos mediante recursos Qt o iconos SVG incluidos en el
proyecto.

------------------------------------------------------------------------

# 7. Panel de inicio

El panel principal debe mostrar tarjetas informativas:

- Equipos recibidos hoy
- Pendientes de diagnóstico
- En reparación
- Esperando aprobación
- Listos para entregar
- Equipos entregados durante el mes
- Saldo pendiente por cobrar
- Ingresos del mes

También debe mostrar:

- Últimas órdenes creadas
- Equipos con entrega estimada próxima
- Órdenes atrasadas
- Actividad reciente

Las tarjetas deben ser clicables para abrir la lista filtrada
correspondiente.

------------------------------------------------------------------------

# 8. Formulario de nueva recepción

Crear un asistente o formulario organizado por secciones.

## 8.1. Datos del cliente

Campos:

    Nombre completo
    Cédula, RUC o identificación
    Teléfono principal
    Teléfono secundario
    Correo electrónico
    Dirección
    Observaciones

Permitir:

- Buscar un cliente ya registrado.
- Autocompletar sus datos.
- Crear un cliente nuevo sin abandonar el formulario.
- Mostrar órdenes anteriores del cliente.
- Evitar duplicados por identificación o teléfono, mostrando una
  advertencia.

## 8.2. Datos del equipo

Campos:

    Tipo de equipo
    Marca
    Modelo
    Número de serie
    Color
    Sistema operativo
    Contraseña o PIN
    Accesorios recibidos
    Estado físico del equipo
    Problema reportado por el cliente
    Observaciones de ingreso

Agregar casillas rápidas para accesorios comunes:

### Laptop

    Cargador
    Batería
    Bolso
    Mouse
    Adaptador
    Memoria USB
    Otro

### Computadora de escritorio

    Cable de corriente
    Monitor
    Teclado
    Mouse
    Parlantes
    Adaptador Wi-Fi
    Otro

### Impresora

    Cable de corriente
    Cable USB
    Cartuchos
    Botellas de tinta
    Bandejas
    Otro

### Cámaras y sistemas de seguridad

    Fuente de alimentación
    Adaptador
    Cable
    Disco duro
    Control remoto
    Mouse
    Antena
    Otro

Permitir escribir accesorios adicionales manualmente.

## 8.3. Recepción

Campos:

    Fecha y hora de ingreso
    Fecha estimada de entrega
    Prioridad
    Técnico responsable
    Costo inicial de diagnóstico
    Anticipo recibido
    Estado inicial

La fecha y hora de ingreso deben completarse automáticamente, pero deben
poder editarse.

## 8.4. Fotografías

Permitir:

- Seleccionar una o varias fotografías.
- Arrastrar y soltar imágenes.
- Pegar una imagen desde el portapapeles.
- Capturar una fotografía desde una cámara web, cuando exista una cámara
  compatible.
- Ver miniaturas.
- Abrir la fotografía en tamaño completo.
- Rotar la fotografía.
- Cambiar su descripción.
- Clasificar el tipo de fotografía.
- Eliminarla de la orden.
- Reordenar las fotografías.

Formatos aceptados:

    JPEG
    PNG
    WEBP
    BMP

Al importar fotografías:

- Crear una copia dentro del directorio de datos del programa.
- No depender de la ubicación original.
- Generar miniaturas.
- Conservar el archivo original cuando sea posible.
- Evitar nombres duplicados mediante UUID.
- Corregir automáticamente la orientación EXIF.
- Comprimir opcionalmente imágenes demasiado grandes.

Ruta sugerida:

    ~/.local/share/lucio-jl-service-manager/attachments/<numero_orden>/

## 8.5. Confirmación

Antes de guardar, mostrar un resumen con:

- Cliente
- Equipo
- Problema reportado
- Accesorios
- Estado físico
- Fotografías
- Fecha de ingreso
- Anticipo
- Número de orden que se generará

Después de guardar, ofrecer:

    Abrir orden
    Imprimir comprobante
    Exportar PDF
    Crear otra recepción

------------------------------------------------------------------------

# 9. Editor de diagnóstico tipo Word

El diagnóstico debe escribirse en un editor enriquecido basado en
`QTextEdit`.

Crear una barra de herramientas con:

- Tipo de letra
- Tamaño de letra
- Negrita
- Cursiva
- Subrayado
- Tachado
- Color del texto
- Color de fondo
- Alineación izquierda
- Centrar
- Alineación derecha
- Justificar
- Lista con viñetas
- Lista numerada
- Aumentar sangría
- Disminuir sangría
- Deshacer
- Rehacer
- Cortar
- Copiar
- Pegar
- Pegar como texto sin formato
- Insertar tabla
- Insertar imagen
- Insertar línea horizontal
- Limpiar formato
- Buscar y reemplazar
- Zoom
- Vista previa de impresión

El contenido debe almacenarse en HTML limpio y compatible con
`QTextDocument`.

Crear editores separados para:

    Diagnóstico técnico
    Trabajo realizado
    Recomendaciones al cliente

El editor debe permitir añadir textos predefinidos, por ejemplo:

    Se realizó inspección visual del equipo.
    Se realizaron pruebas de encendido.
    Se verificó el estado del almacenamiento.
    Se verificó la memoria RAM.
    Se recomienda realizar mantenimiento preventivo.
    Se recomienda reemplazar el componente defectuoso.
    El equipo fue probado y funciona correctamente.

Las plantillas de texto deben poder administrarse desde Configuración.

------------------------------------------------------------------------

# 10. Vista de una orden

La ficha de una orden debe mostrar pestañas:

    Resumen
    Cliente
    Equipo
    Diagnóstico
    Reparación
    Fotografías
    Presupuesto y pagos
    Historial
    Documentos

## Resumen

Mostrar:

- Número de orden
- Estado
- Prioridad
- Cliente
- Teléfono
- Equipo
- Marca
- Modelo
- Número de serie
- Fecha de ingreso
- Fecha estimada
- Saldo pendiente
- Técnico responsable

Incluir botones rápidos:

    Editar
    Cambiar estado
    Añadir nota
    Registrar pago
    Añadir fotografías
    Generar PDF
    Imprimir
    Marcar como entregado

## Historial

Mostrar una línea de tiempo cronológica con:

- Fecha y hora
- Tipo de evento
- Estado
- Usuario
- Comentario
- Cambios realizados

No borrar los eventos históricos cuando se edite la orden.

------------------------------------------------------------------------

# 11. Lista de órdenes

Crear una tabla avanzada con las columnas:

    Número de orden
    Fecha de ingreso
    Cliente
    Teléfono
    Tipo de equipo
    Marca y modelo
    Número de serie
    Problema reportado
    Estado
    Prioridad
    Fecha estimada
    Total
    Saldo

Permitir:

- Ordenar columnas.
- Ocultar o mostrar columnas.
- Cambiar el ancho.
- Guardar la configuración de la tabla.
- Abrir una orden con doble clic.
- Menú contextual.
- Exportar resultados.
- Imprimir la lista.
- Selección múltiple.

Añadir filtros:

    Texto libre
    Número de orden
    Cliente
    Teléfono
    Tipo de equipo
    Marca
    Número de serie
    Estado
    Prioridad
    Técnico
    Rango de fechas
    Con saldo pendiente
    Con retraso

La búsqueda debe ejecutarse al escribir, con un pequeño retraso para
evitar consultas excesivas.

------------------------------------------------------------------------

# 12. Clientes e historial

La ficha de cada cliente debe mostrar:

- Datos personales
- Equipos registrados
- Órdenes anteriores
- Equipos actualmente en reparación
- Pagos realizados
- Saldo pendiente
- Notas
- Fecha de última visita

Permitir abrir cualquier orden anterior.

Agregar una opción para generar un reporte PDF con el historial completo
del cliente.

------------------------------------------------------------------------

# 13. Presupuestos y costos

Permitir añadir conceptos individuales:

    Diagnóstico
    Mano de obra
    Repuesto
    Accesorio
    Servicio
    Otro

Cada concepto debe contener:

    Descripción
    Cantidad
    Precio unitario
    Subtotal

Calcular automáticamente:

    Subtotal
    Descuento
    Impuestos
    Total
    Anticipo
    Pagos realizados
    Saldo pendiente

Permitir configurar si el taller utiliza impuestos.

Para Ecuador, permitir configurar el IVA, pero no fijar permanentemente
un porcentaje en el código. Debe ser un valor editable desde
Configuración.

------------------------------------------------------------------------

# 14. Generación de PDF

El programa debe generar documentos PDF profesionales.

Crear al menos estos tipos:

## 14.1. Comprobante de recepción

Debe incluir:

- Logo del taller
- Nombre del taller
- Nombre del técnico
- Dirección
- Teléfono
- Correo
- Número de orden
- Fecha y hora de ingreso
- Datos del cliente
- Datos del equipo
- Número de serie
- Problema reportado
- Estado físico
- Accesorios recibidos
- Fotografías seleccionadas
- Anticipo
- Saldo
- Fecha estimada de entrega
- Condiciones del servicio
- Espacio para firma del cliente
- Espacio para firma del técnico

## 14.2. Informe técnico

Debe incluir:

- Datos del taller
- Datos del cliente
- Datos del equipo
- Problema reportado
- Diagnóstico técnico
- Trabajo realizado
- Repuestos utilizados
- Recomendaciones
- Fotografías del antes y después
- Costos
- Garantía
- Firmas

## 14.3. Presupuesto

Debe incluir:

- Lista de conceptos
- Cantidades
- Precios
- Subtotales
- Impuestos
- Total
- Vigencia del presupuesto
- Espacio para aprobación del cliente

## 14.4. Comprobante de entrega

Debe incluir:

- Datos de la orden
- Trabajo realizado
- Estado final
- Pagos
- Saldo
- Garantía
- Fecha de entrega
- Declaración de conformidad
- Firma del cliente
- Firma del técnico

## 14.5. Historial completo

Debe contener todos los eventos de la orden en orden cronológico.

Los PDF deben:

- Tener tamaño A4 por defecto.
- Permitir elegir tamaño Carta.
- permitir elegir además tamaño para pantallas de celular 63x110 mm para los clientes que quieran leer el reporte en sus celulares
- Incluir números de página.
- Permitir vista previa.
- Permitir guardar como archivo.
- Permitir enviar directamente a la impresora.
- Dividir correctamente el contenido entre páginas.
- Respetar texto enriquecido, tablas e imágenes.
- Evitar imágenes deformadas.
- Incluir encabezado y pie de página.
- Usar márgenes configurables.

El nombre del archivo debe ser descriptivo, con le fecha y hora, un nombre y un apellido, por ejemplo:

    20260801-153701_Juan-Perez_Informe-Tecnico.docx

------------------------------------------------------------------------

# 15. Impresión

Implementar impresión usando:

    QPrinter
    QPrintDialog
    QPrintPreviewDialog
    QPageLayout
    QPageSize

Permitir:

- Seleccionar impresora.
- Elegir orientación.
- Elegir tamaño de papel.
- Establecer márgenes.
- Imprimir todas las páginas.
- Elegir rango de páginas.
- Establecer número de copias.
- Ver una vista previa antes de imprimir.

------------------------------------------------------------------------

# 16. Reportes

Crear una sección de reportes con filtros por rango de fechas.

Reportes requeridos:

    Equipos ingresados
    Equipos entregados
    Equipos pendientes
    Equipos por tipo
    Equipos por marca
    Órdenes por estado
    Órdenes atrasadas
    Trabajos no reparables
    Ingresos económicos
    Pagos recibidos
    Saldos pendientes
    Clientes frecuentes
    Repuestos utilizados

Permitir exportar los reportes a:

    PDF
    CSV

Los reportes económicos deben mostrar:

    Ingresos por día
    Ingresos por semana
    Ingresos por mes
    Costos de repuestos
    Mano de obra
    Saldo pendiente
    Total cobrado

Añadir gráficos sencillos mediante Qt Charts o matplotlib, manteniendo
esta dependencia como opcional.

------------------------------------------------------------------------

# 17. Copias de seguridad

Crear un sistema de copias de seguridad que incluya:

- Base de datos.
- Fotografías.
- Logo.
- Configuración.
- Plantillas de texto.
- Plantillas de reportes.

Crear copias en formato:

    ZIP

Permitir:

- Crear una copia manual.
- Elegir carpeta de destino.
- Restaurar una copia.
- Verificar la integridad antes de restaurar.
- Crear copias automáticas.
- Conservar las últimas N copias.
- Mostrar fecha y tamaño de cada copia.
- Abrir la carpeta de copias.

Antes de restaurar, crear automáticamente una copia del estado actual.

Mostrar claramente que una restauración reemplazará los datos
existentes.

------------------------------------------------------------------------

# 18. Configuración

Crear una ventana de configuración organizada en categorías:

    Taller
    Técnico
    Numeración
    Tipos de equipos
    Estados
    Costos e impuestos
    Textos predefinidos
    Documentos PDF
    Fotografías
    Copias de seguridad
    Apariencia
    Idioma

## Datos iniciales

Usar:

    Nombre del técnico: Ing. Joseph Lucio
    Moneda: USD
    País: Ecuador

Los demás datos deben quedar editables.

Permitir cargar el logo del taller.

------------------------------------------------------------------------

# 19. Diseño visual

Crear una interfaz limpia y profesional.

Requisitos:

- Diseño moderno.
- Buena legibilidad.
- Espaciado adecuado.
- Botones claramente identificados.
- No saturar la interfaz.
- Adaptarse a resoluciones desde 1366 × 768.
- Permitir maximizar la ventana.
- Recordar tamaño y posición.
- Recordar el estado de paneles y divisores.
- Compatibilidad con tema claro y oscuro.
- No usar colores fijos que impidan el funcionamiento con temas oscuros.
- Respetar la paleta del sistema.
- Usar hojas de estilo QSS solamente cuando sean necesarias.

Mostrar los estados con etiquetas visuales de colores, pero incluir
siempre el texto para no depender solamente del color.

------------------------------------------------------------------------

# 20. Validaciones

Implementar validaciones para:

- Nombre del cliente obligatorio.
- Número de teléfono válido.
- Fecha estimada no anterior a la fecha de ingreso.
- Montos no negativos.
- Anticipo no superior al total, salvo que se maneje como crédito.
- Número de serie duplicado, mostrando advertencia.
- Cliente duplicado, mostrando posibles coincidencias.
- Fotografías en formatos válidos.
- Rutas y nombres de archivos seguros.
- Campos numéricos con `QDoubleValidator`.
- Confirmación antes de eliminar información.

No eliminar permanentemente órdenes por defecto.

Implementar eliminación lógica:

    activo
    fecha_eliminacion

Agregar una papelera desde la que se pueda restaurar una orden.

------------------------------------------------------------------------

# 21. Seguridad y privacidad

La aplicación debe:

- Funcionar completamente sin internet.
- No enviar datos a servidores externos.
- No registrar contraseñas del equipo en los logs.
- Proteger campos sensibles.
- Escapar correctamente el HTML mostrado.
- Evitar inyección SQL usando SQLAlchemy.
- Confirmar operaciones destructivas.
- Evitar que una fotografía importada pueda sobrescribir otro archivo.
- Ocultar la contraseña o PIN mediante un campo de contraseña.

Preparar la arquitectura para añadir usuarios y roles en el futuro,
aunque la primera versión pueda funcionar con un solo usuario.

------------------------------------------------------------------------

# 22. Registro de errores

Crear logs en:

    ~/.local/state/lucio-jl-service-manager/logs/

Registrar:

- Inicio y cierre del programa.
- Errores de base de datos.
- Fallos al importar imágenes.
- Fallos de generación de PDF.
- Fallos en copias de seguridad.
- Excepciones no controladas.

No registrar:

- Contraseñas.
- PIN.
- Información sensible innecesaria.

Implementar un manejador global de excepciones que muestre al usuario un
mensaje comprensible.

------------------------------------------------------------------------

# 23. Internacionalización

Preparar el programa para traducciones con:

    QTranslator
    pylupdate6
    linguist
    lrelease

Idioma inicial:

    Español

Preparar al menos las traducciones para:

    Español
    Inglés

No escribir los textos visibles directamente en lugares difíciles de
traducir.

------------------------------------------------------------------------

# 24. Accesibilidad y usabilidad

Implementar:

- Navegación mediante teclado.
- Orden de tabulación correcto.
- Atajos de teclado.
- Etiquetas asociadas a cada campo.
- Descripciones emergentes.
- Mensajes de error comprensibles.
- Confirmaciones claras.
- Tamaño de fuente configurable.
- Buen contraste.
- Indicadores visibles de campos obligatorios.

Atajos sugeridos:

    Ctrl+N    Nueva recepción
    Ctrl+F    Buscar
    Ctrl+S    Guardar
    Ctrl+P    Imprimir
    Ctrl+Shift+P    Vista previa
    Ctrl+B    Negrita
    Ctrl+I    Cursiva
    Ctrl+U    Subrayado
    F5        Actualizar
    Esc       Cerrar diálogo

------------------------------------------------------------------------

# 25. Pruebas

Crear pruebas automatizadas para:

- Creación de clientes.
- Creación de equipos.
- Creación de órdenes.
- Generación del número de orden.
- Cambio de estado.
- Registro del historial.
- Cálculo de costos.
- Cálculo de saldo.
- Registro de pagos.
- Importación de fotografías.
- Creación y restauración de copias.
- Generación de PDF.
- Validaciones.
- Migraciones de base de datos.

Usar una base de datos temporal durante las pruebas.

------------------------------------------------------------------------

# 26. Empaquetado

Preparar el proyecto para crear:

    Paquete .deb
    AppImage
    Ejecutable para Windows

Para Debian:

- Usar rutas compatibles con XDG.
- No escribir en `/usr` durante la ejecución.
- Incluir archivo `.desktop`.
- Incluir iconos en diferentes tamaños.
- Incluir metadatos AppStream.
- Incluir licencia.
- Incluir manual básico.
- Declarar correctamente las dependencias.
- Evitar descargar dependencias durante la ejecución.

Crear un archivo de escritorio similar a:

    [Desktop Entry]
    Type=Application
    Name=Lucio JL Mantenimiento 
    Comment=Gestión de recepción y reparación de equipos
    Exec=lucio-jl-service-manager
    Icon=lucio-jl-service-manager
    Categories=Office;Utility;
    Terminal=false

------------------------------------------------------------------------

# 27. README

Crear un README completo con:

- Descripción.
- Características.
- Capturas de pantalla provisionales.
- Requisitos.
- Instalación en entorno virtual.
- Ejecución.
- Pruebas.
- Estructura del proyecto.
- Creación del paquete.
- Ubicación de datos.
- Creación de copias de seguridad.
- Restauración.
- Resolución de problemas.
- Licencia.

## Incluir instrucciones

para Windows con python y para lanzar:

python -m luciotech.main

No usar venv porque no es necesario
    
Y para Linux sin pip pues se usarán los paquetes python de los repositorios, y para lanzar 

python3 -m luciotech.main

Para macOS semejante

------------------------------------------------------------------------

# 28. Metodología de implementación

No intentes construir todo en un solo paso.

Trabaja por fases y mantén siempre una versión ejecutable.

## Fase 1

Crear:

- Estructura del proyecto.
- Ventana principal.
- Base de datos.
- Modelos.
- Clientes.
- Equipos.
- Nueva recepción.
- Lista de órdenes.
- Vista básica de una orden.

## Fase 2

Crear:

- Editor enriquecido.
- Diagnóstico.
- Trabajo realizado.
- Recomendaciones.
- Historial.
- Estados.
- Fotografías.

## Fase 3

Crear:

- Presupuestos.
- Pagos.
- Cálculos.
- PDF.
- Impresión.
- Comprobante de recepción.
- Informe técnico.

## Fase 4

Crear:

- Reportes.
- Copias de seguridad.
- Configuración.
- Temas.
- Traducciones.
- Empaquetado.

Después de cada fase:

1.  Ejecuta la aplicación.
2.  Corrige los errores.
3.  Ejecuta las pruebas.
4.  Actualiza el README.
5.  Realiza un commit Git descriptivo.

------------------------------------------------------------------------

# 29. Forma de trabajar

Antes de escribir código:

1.  Analiza todos los requisitos.
2.  Propón la arquitectura definitiva.
3.  Presenta el modelo de base de datos.
4.  Enumera las pantallas.
5.  Identifica riesgos técnicos.
6.  Divide el trabajo en tareas pequeñas.

Después comienza con la Fase 1.

No generes archivos vacíos sin propósito.

No uses pseudocódigo cuando sea posible implementar código funcional.

Cada módulo debe incluir:

- Tipos de datos.
- Docstrings.
- Manejo de errores.
- Nombres claros.
- Separación de responsabilidades.

Utiliza:

    from __future__ import annotations

Añade anotaciones de tipo.

Evita funciones demasiado largas y clases con demasiadas
responsabilidades.

------------------------------------------------------------------------

# 30. Resultado esperado inicial

En la primera implementación funcional debe ser posible:

1.  Abrir el programa.
2.  Crear o seleccionar un cliente.
3.  Registrar un equipo.
4.  Crear una orden de ingreso.
5.  Añadir el problema reportado.
6.  Añadir fotografías.
7.  Guardar la orden.
8.  Consultarla desde la lista.
9.  Escribir un diagnóstico enriquecido.
10. Cambiar el estado.
11. Consultar el historial.
12. Generar un comprobante de recepción en PDF.
13. Imprimirlo.
14. Cerrar y volver a abrir el programa sin perder datos.

Comienza mostrando:

- La arquitectura propuesta.
- El esquema de la base de datos.
- Las decisiones técnicas.
- El plan de implementación.

Después crea los archivos correspondientes a la Fase 1 y proporciona
instrucciones exactas para instalar y ejecutar el proyecto.
