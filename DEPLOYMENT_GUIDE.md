# JMEJCat - Guía de Despliegue Portable

## Problema Común: El executable no inicia en ordenadores sin Python/Conda

### Síntomas
```
JMEJCat ya está ejecutando (PID: XXXX)!
```
O el programa simplemente no inicia sin errores visibles.

### Causa Principal
1. **Lock file de instancia anterior**: El archivo `~/.jmejcat.lock` indica que otra instancia está en ejecución
2. **DLLs faltantes**: Falta Visual C++ Redistributable o DLLs de Miniconda
3. **Executable antiguo**: Se está ejecutando una versión vieja construida con conda

---

## Solución Paso a Paso

### Paso 1: Cerrar todas las instancias
```batch
taskkill /IM JMEJCat.exe /F 2>nul
```

### Paso 2: Eliminar lock file
```batch
del "%USERPROFILE%\.jmejcat.lock"
```

### Paso 3: Verificar Visual C++ Redistributable
Descargar e instalar si no está:
- https://aka.ms/vs/17/release/vc_redist.x64.exe

### Paso 4: Si tiene Miniconda en otro PC, copiar DLLs
Ejecutar `copy_miniconda_dlls.bat` para copiar las DLLs necesarias.

---

## Cómo Reconstruir el Executable

### Requisitos
- Miniconda3 o Python 3.12+ con:
  - PySide6
  - Pillow
  - PyInstaller

### Pasos para rebuild

1. **Abrir terminal en la carpeta del proyecto**
```batch
cd C:\Users\JM DJ\Documents\program2\JMEJCat\JMEJCat
```

2. **Ejecutar script de build**
```batch
build_jmejcat.bat
```

3. **Copiar DLLs de Miniconda** (importante para portability)
```batch
copy_miniconda_dlls.bat
```

4. **El executable portable estará en:**
```
JMEJCat\JMEJCat_Portable\JMEJCat\JMEJCat.exe
```

---

## Archivos de Diagnóstico Incluidos

| Archivo | Descripción |
|---------|-------------|
| `diagnostic.bat` | Verifica DLLs, lock files y errores |
| `copy_miniconda_dlls.bat` | Copia DLLs de Miniconda al executable |
| `build_jmejcat.bat` | Construye el executable portable |

---

## Estructura del Paquete Portable

```
JMEJCat_Portable/
├── JMEJCat/
│   ├── JMEJCat.exe          # Executable principal
│   ├── _internal/           # DLLs y dependencias
│   │   ├── python313.dll
│   │   ├── Qt6*.dll
│   │   ├── VCRUNTIME*.dll
│   │   ├── data/            # Base de datos
│   │   └── ...
│   ├── assets/              # Iconos
│   └── logs/                # Logs (se crean al ejecutar)
├── diagnostic.bat           # Script de diagnóstico
├── copy_miniconda_dlls.bat # Copiar DLLs (si tiene Miniconda)
└── README.txt               # Instrucciones básicas
```

---

## Troubleshooting

### Error: "JMEJCat ya está ejecutando"
- Ya hay una instancia en ejecución
- Solución: `taskkill /IM JMEJCat.exe /F` y `del "%USERPROFILE%\.jmejcat.lock"`

### Error: "DLL no encontrada"
- Falta VC++ Redistributable
- Instalar desde: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Error: Silent crash (no abre, no da errores)
- Probablemente faltan DLLs de Miniconda
- Ejecutar `copy_miniconda_dlls.bat` si tiene Miniconda
- Verificar logs en: `%USERPROFILE%\.jmejcat_logs\`

### Logs
Los archivos de log están en:
- Con Python: `%USERPROFILE%\.jmejcat_logs\`
- Portable: `logs/` dentro de la carpeta del executable

---

## Notas Técnicas

### Por qué PyInstaller + Miniconda causa problemas
- Miniconda incluye dependencias de runtime de Anaconda
- El executable arrastra `conda` y `anaconda` en las dependencias
- Solución: Usar DLLs de Miniconda explícitamente o Python puro

### DLLs Críticas Requeridas
- `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`
- `MSVCP140.dll`, `MSVCP140_1.dll`, `MSVCP140_2.dll`
- `ucrtbase.dll`
- `python313.dll`
- `Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll`

---

## Checklist antes de Distribuir

- [ ] Ejecutar `build_jmejcat.bat`
- [ ] Ejecutar `copy_miniconda_dlls.bat`
- [ ] Probar el executable en el ordenador actual
- [ ] Copiar carpeta `JMEJCat_Portable` completa
- [ ] Verificar que el usuario tenga VC++ Redistributable
- [ ] Instruir al usuario para cerrar instancias anteriores

---

Fecha de creación: 2026-03-19
Versión: 1.0
