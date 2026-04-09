# CFC Store — Generar un ejecutable Windows (.exe)

Este proyecto es una pequeña app Flask que usa SQLite para almacenar los datos.

Objetivo
- Empaquetar la aplicación como un único `.exe` que se pueda ejecutar en un PC Windows.
- Asegurar que la base de datos y archivos de usuario se guarden localmente en la máquina (persistencia tras apagar).

Comportamiento de almacenamiento
- Por defecto, cuando se ejecuta en Windows la base de datos se guarda en:

  `%LOCALAPPDATA%\\CFC_STORE\\database.db`

  Esto garantiza que los datos queden en la cuenta de usuario y sobrevivan a reinicios.
- Puedes forzar una ubicación diferente exportando la variable de entorno `CFC_STORE_DATA_DIR` antes de ejecutar la app:

  ```powershell
  setx CFC_STORE_DATA_DIR "C:\ruta\a\datos\CFC_STORE"
  ```

Instrucciones para crear el `.exe` (en un PC Windows)
1. Instalar Python 3.11 (la misma versión que usas para desarrollar).
2. Clonar/copiar el proyecto en la máquina Windows.
3. Abrir PowerShell o CMD en la carpeta del proyecto.
4. (Opcional) Crear un venv y activarlo:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

5. Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

6. Construir el ejecutable usando PyInstaller (el siguiente comando empaqueta `templates` y `static`):

```powershell
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
```

- Después del build el executble estará en `dist\app.exe`.
- Nota: el `--add-data` usa `;` como separador en Windows. Si tus assets están en otras carpetas, añádelas también.

Ejecución del `.exe`
- Copia `dist\app.exe` a la máquina Windows y ejecútalo. En el primer arranque la app creará la carpeta de datos en `%LOCALAPPDATA%\\CFC_STORE` y creará `database.db` con el esquema inicial.
- Para cambiar la carpeta de datos en tiempo de ejecución, exporta `CFC_STORE_DATA_DIR` antes de ejecutar.

Construir desde macOS o Linux
- Es preferible construir el .exe en una máquina Windows o en una VM Windows. PyInstaller no produce executables Windows confiables cuando se ejecuta desde macOS/linux (cross-compiling no soportado oficialmente).

Sugerencias
- Si vas a distribuir la app a usuarios no técnicos considera crear un instalador (Inno Setup) que coloque `app.exe` en `Program Files` y cree accesos directos; la base de datos seguirá estando en `%LOCALAPPDATA%`.
- Para actualizaciones y backups, simplemente copia la carpeta `%LOCALAPPDATA%\\CFC_STORE`.

Si quieres, puedo:
- Crear y ajustar un spec de PyInstaller más fino.
- Generar el `.exe` por ti si me facilitas una máquina Windows o me autorizas a usar un builder (nota: aquí no puedo construir para Windows directamente en tu macOS).