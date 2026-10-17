# Filtro Alebrije

Filtro facial de **realidad aumentada** para el navegador del teléfono. Al abrir la página se enciende la cámara frontal, se detecta tu rostro y se cubre con una **máscara de alebrije oaxaqueño** animada que diseñé, modelé y animé en **Blender**. La máscara sigue los giros de tu cabeza y reacciona a tus gestos.

> Actividad 2 · Realidad Virtual y Aumentada · 2026

| Máscara animada | Reacción a "abre la boca" |
|---|---|
| ![Máscara](docs/capturas/mascara.png) | ![Rugido](docs/capturas/rugido.png) |

## Gestos

| Gesto | Señal de MediaPipe | Reacción |
|---|---|---|
| 😮 Abrir la boca | `jawOpen > 0.5` | **Rugido:** explosión de confeti desde el hocico, la máscara late y suena un rugido |
| 🤨 Subir las cejas | `browInnerUp > 0.55` | El alebrije **cambia de colores** (5 paletas) con campanitas |
| 😑 Parpadear fuerte | `eyeBlinkLeft` y `eyeBlinkRight > 0.6` | Los ojos **brillan** y sueltan chispas |

Cada gesto usa un disparador con umbral, un rearme por debajo de 0.3 y una pausa mínima de 0.8 a 1.2 s (`js/gestos.js`), para que un gesto sostenido no dispare varias veces. Los chips de la parte inferior se iluminan con cada disparo.

## La máscara (Blender)

`blender/mascara_alebrije.py` construye todo por código dentro de Blender, así que el resultado se puede reproducir. El archivo editable es `blender/mascara_alebrije.blend`.

- **Casco:** elipsoide recortado y con grosor que cubre el rostro completo del modelo canónico de MediaPipe (15.5 × 17.7 cm) con margen.
- **Textura propia:** bandas en zigzag con contorno negro y puntos, al estilo de los alebrijes de San Martín Tilcajete. Se genera con NumPy y va empacada en el GLB.
- **Detalles:** hocico, fosas nasales, colmillos, ojos de reptil con iris emisivo, orejas, cuernos en espiral y cresta.
- **Animación de 2 s en bucle (24 fps):** las orejas aletean, los cuernos se mecen, la cresta hace una ola, los ojos miran de lado a lado y parpadean, y el hocico respira.
- **Medidas:** se modela en centímetros y en el mismo espacio que el modelo canónico de MediaPipe, así que encaja con la matriz de transformación facial sin ajustes.

Para regenerar la máscara:

```bash
blender --background --python blender/mascara_alebrije.py
```

## Cómo funciona

1. `getUserMedia` abre la cámara frontal en cuanto carga la página, sin pantallas intermedias.
2. **MediaPipe Face Landmarker** (`@mediapipe/tasks-vision`) devuelve en cada cuadro la matriz de transformación facial y 52 blendshapes.
3. La máscara cuelga de un grupo de three.js cuya matriz es la matriz facial, con un suavizado ligero (lerp/slerp 0.65) contra el temblor. Se ve con una cámara de 63° de FOV vertical, la misma que usa MediaPipe.
4. El video y el canvas comparten `object-fit: cover` y el efecto espejo, así que el recorte y la alineación coinciden en cualquier pantalla.

## Herramientas

- Blender 5.2 (Python `bpy`): modelado, textura y animación.
- MediaPipe Tasks Vision 0.10.14: Face Landmarker con blendshapes.
- three.js 0.160: render, GLTFLoader y AnimationMixer.
- Web Audio API: efectos sintetizados.

## Instalación y uso

```bash
git clone <url-del-repo> && cd 02-filtro-alebrije
npx serve .
```

- La cámara requiere **HTTPS** o `localhost`. Para el teléfono, publica la carpeta en **Vercel** o **Cloudflare Pages** (sitio estático, sin build).
- La primera vez que tocas la pantalla se activa el sonido (los navegadores lo exigen).
- Modo demo sin cámara: `index.html?demo`. Teclas 1, 2 y 3 para probar las reacciones.
- Modo foto: `index.html?imagen=ruta/a/foto.jpg` aplica el filtro a una imagen fija.
- Prueba del disparador de gestos: `node js/gestos.test.mjs`.

## Estructura

```
index.html                    video, canvas y chips de gestos
css/styles.css
js/main.js                    cámara, detección, seguimiento, reacciones
js/gestos.js                  disparador con umbral, rearme y pausa
js/audio.js                   efectos con Web Audio
assets/mascara_alebrije.glb   máscara exportada desde Blender
blender/                      script y .blend fuente
```

## Créditos y licencias

| Recurso | Autor / fuente | Licencia |
|---|---|---|
| Código, máscara, textura y animación | Carlos Antonio Gómez Morales | MIT (ver `LICENSE`) |
| Efectos de sonido | Sintetizados en código, autoría propia | MIT |
| MediaPipe Tasks Vision y modelo Face Landmarker | Google | Apache 2.0 |
| three.js | three.js authors | MIT |
| Blender | Blender Foundation | GPL (la herramienta; el contenido creado es propio) |
