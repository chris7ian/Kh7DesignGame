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

Para generar ejecutables nativos puedes usar [pyinstaller](https://pyinstaller.org/en/stable/):

```bash
pip install pyinstaller
pyinstaller src/main.py --onefile --name SpaceOdyssey2D
```

Esto generará un ejecutable en `dist/SpaceOdyssey2D`. Repite el proceso en cada plataforma para obtener los binarios nativos.

## Créditos

Desarrollado por request del usuario. Si reutilizas este proyecto, ¡menciona la fuente!

