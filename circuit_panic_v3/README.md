# Circuit Panic

Prueba de concepto académica de un serious game para evaluar habilidades de resolución de problemas mediante **stealth assessment**.

## Requisitos

- Python 3.10+
- pygame 2.x

Instalación:

```bash
pip install pygame
```

## Ejecución

Desde la carpeta del proyecto:

```bash
python main.py
```

## Controles

- Click izquierdo sobre un nodo: inspeccionar.
- Botón **REPARAR**: intenta reparar el nodo seleccionado.
- Click derecho sobre un nodo: intenta reparar directamente.
- Tecla **R**: intenta reparar el nodo seleccionado.
- **Enter/Espacio**: continuar entre niveles.
- **F11**: alternar pantalla completa.
- **Esc**: salir.

## Reporte PDF final

Al terminar los tres niveles aparece la pantalla de resultados con dos opciones:

- **Reiniciar**: vuelve a empezar la partida.
- **Finalizar y generar PDF**: genera un reporte organizado con los datos completos del stealth assessment y cierra el juego.

El PDF se guarda automáticamente en:

```text
reports/reporte_stealth_circuit_panic_YYYYMMDD_HHMMSS.pdf
```

También puedes presionar la tecla **F** en la pantalla de resultados para finalizar y generar el PDF.

## Stealth assessment

El juego registra silenciosamente por nivel:

- tiempo total
- intentos incorrectos
- nodos inspeccionados
- primer intento correcto
- ratio de eficiencia
- tiempo hasta primer intento
- backtracking
- score de resolución de problemas

El jugador solo ve un score y retroalimentación cualitativa. Los datos completos se imprimen en consola y quedan documentados en el reporte PDF final.

## Estructura

```text
circuit_panic_v3/
├── main.py
├── game.py
├── stealth.py
├── renderer.py
├── report_generator.py
├── constants.py
├── README.md
└── reports/          # Se crea automáticamente al finalizar el juego
```
