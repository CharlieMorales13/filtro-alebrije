# Me convertí en zorro de fiesta: filtro facial con Meshy, Blender y MediaPipe 🦊

*Borrador para LinkedIn (≈400 palabras). Agrega el video o GIF y cambia los enlaces antes de publicar.*

---

Las máscaras de danza y los alebrijes de San Martín Tilcajete son de lo más bonito que tiene Oaxaca, así que para la segunda actividad de Realidad Virtual y Aumentada me propuse ponerme una máscara así en la cara.

🎯 **Objetivo**
Hacer un filtro de RA que, al abrir la app, detecte el rostro con la cámara frontal y lo cubra con una máscara animada de diseño propio que siga sus movimientos y reaccione a gestos.

🛠️ **Herramientas**
- Meshy AI para generar el modelo base a partir de mi prompt.
- Blender 5.2 para optimizar la máscara, ajustarla a la cara, crearle un esqueleto y animarla, todo con un script de Python.
- MediaPipe Face Landmarker para detectar el rostro y sus 52 blendshapes.
- three.js para renderizar el GLB animado.
- Web Audio API para los efectos de sonido.

🎨 **Proceso**
1. Diseñé un zorro de fiesta con pintura de alebrije, plumas y flecos de listón, inspirado en las máscaras de danza oaxaqueñas, y generé la base en Meshy.
2. En Blender bajé la malla de 200 k a 40 k caras y la coloqué en el espacio del modelo facial canónico de MediaPipe, en centímetros, con los huecos de los ojos justo sobre los ojos. Le hice un esqueleto de 8 huesos y la animé en un ciclo de 2 s: flecos que se mecen, plumas que ondean y orejas que dan un tirón.
3. Exporté a GLB y en la web lo colgué de la matriz facial con un suavizado ligero para quitar el temblor sin meter retraso.
4. Programé tres gestos. Abrir la boca lanza un rugido con confeti. Subir las cejas cambia los colores de la máscara. Parpadear fuerte la hace destellar en dorado.

🧩 **Retos**
- **De 13.6 MB a 2.3 MB:** el modelo de Meshy era demasiado pesado para un teléfono; reducirlo sin perder la pintura fue clave.
- **Alinear la máscara:** el video y el canvas tienen que recortarse igual (`object-fit: cover`) y reflejarse igual; si no, la máscara "flota" al lado de la cara.
- **Disparos repetidos:** al mantener la boca abierta, el efecto se disparaba en cada cuadro. Lo resolví con un umbral, un rearme y una pausa mínima entre disparos.
- **Abrir directo al filtro:** nada de menús; la cámara se pide al cargar la página. El sonido se activa con el primer toque porque los navegadores lo exigen.
- **Pruebas:** agregué un modo demo y un modo foto para probar sin cámara y con distintas caras.

✅ **Resultado**
Un filtro web que abre directo en la cámara, cubre toda la cara, sigue los giros de la cabeza y responde a tres gestos. Me dejó claro cuánto trabajo hay detrás de un filtro "sencillo" de Instagram.

🎥 [video / GIF aquí]
💻 Repositorio: https://github.com/CharlieMorales13/filtro-alebrije
🔗 Pruébalo: https://filtro-alebrije.carlos-gomez-dev13.workers.dev/

#RealidadAumentada #Blender #MediaPipe #threejs #Oaxaca #Alebrijes #Meshy #FiltrosAR
