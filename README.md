# Interte11ar

Un videojuego 2D de temática espacial creado con Python y Pygame, compatible con macOS y Windows.

## Requisitos

- Python 3.10 o superior  
- `pip` actualizado (`python -m pip install --upgrade pip`)

## Instalación

### macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Ejecución recomendada (usa importaciones relativas correctas)
python -m src.main

# Alternativa si prefieres ejecutar el archivo directamente
python src/main.py
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Ejecución recomendada
python -m src.main

# Alternativa si prefieres ejecutar el archivo directamente
python src\main.py
```

## Jugabilidad

- Controla la nave con las teclas `←` y `→`.
- Dispara proyectiles con la barra espaciadora.
- Evita los meteoritos (ahora de tamaños variados) y destrúyelos para sumar puntos.
- Si recibes daño, la nave parpadea durante ~2 s y no puede ser golpeada de nuevo mientras dura la invulnerabilidad.
- La dificultad aumenta gradualmente con más meteoritos y velocidad.
- Observa en la parte inferior un minimapa que muestra una franja más amplia (con mayor vista hacia la derecha) para anticipar meteoritos antes de que entren en pantalla.

## Estructura del proyecto

```
src/
  main.py          # Punto de entrada del juego
  settings.py      # Constantes y configuración
  entities.py      # Lógica de la nave, meteoritos y proyectiles
  ui.py            # Interfaz de usuario (HUD)
assets/
  fonts/           # Tipografías opcionales
  sounds/          # Efectos de sonido opcionales
```

Los directorios `assets/fonts` y `assets/sounds` pueden poblarse con tus propios recursos en formato `.ttf` y `.wav`.

## Controles

- `←` / `→`: mover la nave
- `Espacio`: disparar
- `Esc`: pausar o salir (desde la pantalla de pausa)

## Compilación / Distribución

### macOS: aplicación .app para abrir con doble clic (sin instalador)

Para obtener un **standalone** que puedas arrastrar a Aplicaciones y abrir con doble clic:

```bash
pip install -r requirements.txt pyinstaller
chmod +x build_mac_app.sh
./build_mac_app.sh
```

Se generará **`dist/Interste11ar.app`**. Puedes moverla a Aplicaciones o a cualquier carpeta; no hace falta instalador. La configuración (opciones) se guarda en `~/Library/Application Support/Interste11ar/`.

### Otras plataformas / ejecutable de consola

Con [PyInstaller](https://pyinstaller.org/en/stable/):

```bash
pip install pyinstaller
pyinstaller --windowed --name Interste11ar --add-data "assets:assets" run_game.py
```

En macOS esto produce `dist/Interste11ar.app`. En Windows usa `;` en lugar de `:` en `--add-data` (p. ej. `assets;assets`).

## Cambiar el icono

- **Icono de la ventana del juego** (y del .app cuando se ejecuta): sustituye o crea **`assets/icon.png`**. Debe ser un PNG (p. ej. 256×256 o 512×512). Se usa en la barra de título y en el Dock mientras el juego está abierto.

- **Icono del .app en Finder** (macOS): crea un archivo **`icon.icns`** en la raíz del proyecto y vuelve a ejecutar `./build_mac_app.sh`. El script usará ese icono para `Interste11ar.app`.

  Para generar `.icns` desde un PNG en Mac:
  1. Crea una carpeta `icon.iconset`.
  2. Añade tu PNG en varios tamaños (p. ej. con [Image2Icon](https://apps.apple.com/app/image2icon/id411461952) o en terminal):
     ```bash
     mkdir icon.iconset
     sips -z 16 16     assets/icon.png --out icon.iconset/icon_16x16.png
     sips -z 32 32     assets/icon.png --out icon.iconset/icon_16x16@2x.png
     sips -z 32 32     assets/icon.png --out icon.iconset/icon_32x32.png
     sips -z 64 64     assets/icon.png --out icon.iconset/icon_32x32@2x.png
     sips -z 128 128   assets/icon.png --out icon.iconset/icon_128x128.png
     sips -z 256 256   assets/icon.png --out icon.iconset/icon_128x128@2x.png
     sips -z 256 256   assets/icon.png --out icon.iconset/icon_256x256.png
     sips -z 512 512   assets/icon.png --out icon.iconset/icon_256x256@2x.png
     sips -z 512 512   assets/icon.png --out icon.iconset/icon_512x512.png
     sips -z 1024 1024 assets/icon.png --out icon.iconset/icon_512x512@2x.png
     iconutil -c icns icon.iconset -o icon.icns
     rm -rf icon.iconset
     ```
  3. Deja **`icon.icns`** en la raíz del proyecto y ejecuta `./build_mac_app.sh`.

## Créditos

Desarrollado por Kh7Designs y Kh7Studios. 
Desarrollado por Christian Tuohy como hobby, para iniciar en la creacion de desarrollo de juegos.
Si reutilizas este proyecto, ¡menciona la fuente!

