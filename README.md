# JMEJCat - Gestión de Apuntes y Expedientes

![Versión](https://img.shields.io/badge/versión-3.57-blue)
![Python](https://img.shields.io/badge/python-3.13%2B-green)
![License](https://img.shields.io/badge/licencia-LGPL%20v3-lightgrey)

JMEJCat es una aplicación de escritorio, portable y offline, diseñada para la **gestión de apuntes y el control de expedientes de un tramitador en un juzgado de lo civil de Barcelona**. Permite organizar la información en formato estructurado, con soporte para imágenes, texto enriquecido y un módulo específico de tramitación de expedientes (número, año, recordatorios y alarmas).

## 🚀 Características Principales

### 📝 Notas Estructuradas
- **Título**: Campo indexable para búsqueda rápida
- **Petición**: Descripción del problema o requerimiento
- **Solución**: Explicación detallada de la solución
- **Ejemplos**: Casos de uso o ejemplos concretos

### 🖼️ Gestión de Imágenes
- **Sistema de archivos**: Imágenes almacenadas como archivos (no en la BD)
- **Miniaturas automáticas**: Generación automática de thumbnails
- **Visor integrado**: Click en miniatura para ver imagen completa
- **Nombres únicos**: Hash SHA256 para evitar colisiones

### 🎨 Interfaz de Usuario
- **PySide6 (Qt6)**: Interfaz nativa y moderna
- **Formato rico**: Negrita, cursiva, subrayado (Ctrl+B, Ctrl+I, Ctrl+U)
- **Búsqueda instantánea**: Filtrado en tiempo real (Ctrl+F)
- **Atajos de teclado**: Productividad mejorada

### 💾 Portabilidad y Seguridad
- **Todo en una carpeta**: Copia la carpeta `data/` y listo
- **Backup automático**: Copias de seguridad al iniciar/cerrar
- **Offline**: No requiere conexión a internet
- **SQLite**: Base de datos local y eficiente

## 📋 Requisitos del Sistema

- **Windows 10/11** 64-bit
- **Python 3.13+** (recomendado via Miniconda)
- **4GB RAM** mínimo, 8GB recomendado
- **100MB** de espacio libre en disco

## 🛠️ Instalación y Uso

### Opción 1: Entorno Conda (Recomendado)

```bash
# 1. Instalar Miniconda (Python 3.12)
# Descarga desde: https://docs.conda.io/en/latest/miniconda.html

# 2. Crear entorno
conda create -n jm_pyside_313 python=3.13
conda activate jm_pyside_313

# 3. Instalar dependencias
pip install PySide6 Pillow

# 4. Clonar o descargar JMEJCat
git clone <repositorio>
cd JMEJCat

# 5. Verificar entorno
check_conda_env.bat

# 6. Ejecutar
python jmejcat.py