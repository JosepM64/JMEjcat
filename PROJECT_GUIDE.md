# JMEJCat - Guía de Desarrollo Rápido

## Para continuar el proyecto

Copia y pega este texto al iniciar:

```
Este es el proyecto JMEJCat (v3.20), aplicación de notas estructuradas Python/PySide6.

Para entender el proyecto rápidamente:
1. Lee primero los archivos .py principales
2. Ejecuta la verificación: python verify_automatica.py

Archivos clave:
- verify_automatica.py (55 verificaciones)
- jmejcat.py (punto de entrada)
- ui_window.py (ventana principal)
- database.py (gestión de notas)
```

---

## Resumen del Proyecto

JMEJCat es una **aplicación de notas estructuradas** desarrollada en Python con PySide6 (Qt6) para Windows.

### Tecnología Principal
- **Lenguaje**: Python 3.x
- **UI Framework**: PySide6 (Qt6)
- **Base de Datos**: SQLite
- **Exportación**: PDF
- **Imágenes**: Pillow

### Estructura Clave
```
JMEJCat/
├── jmejcat.py                  # Punto de entrada
├── ui_window.py                # Ventana principal (MainWindow)
├── database.py                 # Gestión de notas (Database)
├── tramitacio_window.py        # Ventana de tramitación
├── tramitacio_database.py       # BD de tramitación
├── calculator.py               # Calculadora
├── pdf_exporter.py             # Exportador PDF
├── image_manager.py            # Gestor de imágenes
├── config.py                   # Configuración
└── utils.py                    # Utilidades
```

---

## Checklist de Verificación (obligatorio antes de cada release)

Ejecutar siempre antes de publicar:
```bash
python verify_automatica.py
```

Debe mostrar: **[OK] PASADOS: 55** (o más)

---

## Estado de Funcionalidades (v3.21)

### ✅ Funcionando
- Verificación automatizada (55 tests)
- Gestión de notas estructuradas
- Base de datos SQLite
- Galería de imágenes
- Exportación PDF
- Calculadora
- Módulo de tramitación

### ⚠️ Pendiente / Notas
- [ ] Testing manual completo

---

## Para Hacer Cambios

1. **Editar código**: Modificar archivos principales
2. **Probar locally**: `python jmejcat.py` (con PySide6 instalado)
3. **Verificar**: `python verify_automatica.py`

---

## Para Retomar el Proyecto

Texto para copiar:

```
Este es JMEJCat v3.21, aplicación de notas Python/PySide6.

Proyecto: JMEJCat
Versión: 3.21
Stack: Python + PySide6 + SQLite + Pillow

Archivos clave:
- verify_automatica.py (55 verificaciones)
- jmejcat.py (entrada)
- ui_window.py (ventana principal)

Verificación: python verify_automatica.py

Entorno: Python 3.x + PySide6
```

---

**Última actualización:** 2026-04-17
**Versión:** 3.20
