# Me convertí en alebrije: filtro facial con Blender y MediaPipe 🐉

*Borrador para LinkedIn (≈400 palabras). Agrega el video o GIF y cambia los enlaces antes de publicar.*

---

Los alebrijes de San Martín Tilcajete son de lo más bonito que tiene Oaxaca, así que para la segunda actividad de Realidad Virtual y Aumentada me propuse ponerme uno en la cara.

🎯 **Objetivo**
Hacer un filtro de RA que, al abrir la app, detecte el rostro con la cámara frontal y lo cubra con una máscara animada de diseño propio que siga sus movimientos y reaccione a gestos.

🛠️ **Herramientas**
- Blender 5.2 para modelar, texturizar y animar la máscara, todo con un script de Python.
- MediaPipe Face Landmarker para detectar el rostro y sus 52 blendshapes.
- three.js para renderizar el GLB animado.
- Web Audio API para los efectos de sonido.

🎨 **Proceso**
1. Diseñé la máscara en el mismo espacio del modelo facial canónico de MediaPipe, en centímetros. Así la matriz de transformación facial la coloca en su lugar sin ajustes manuales.
2. Generé una textura de zigzags, contornos y puntos, como los alebrijes tallados en copal, y la animé en un ciclo de 2 s: orejas que aletean, cuernos que se mecen, una cresta que hace la ola, ojos que miran y parpadean.
3. Exporté a GLB y en la web lo colgué de la matriz facial con un suavizado ligero para quitar el temblor sin meter retraso.
4. Programé tres gestos. Abrir la boca lanza un rugido con confeti. Subir las cejas cambia los colores del alebrije. Parpadear fuerte hace brillar los ojos.

🧩 **Retos**
- **Alinear la máscara:** el video y el canvas tienen que recortarse igual (`object-fit: cover`) y reflejarse igual; si no, la máscara "flota" al lado de la cara.
- **Disparos repetidos:** al mantener la boca abierta, el efecto se disparaba en cada cuadro. Lo resolví con un umbral, un rearme y una pausa mínima entre disparos.
- **Abrir directo al filtro:** nada de menús; la cámara se pide al cargar la página. El sonido se activa con el primer toque porque los navegadores lo exigen.
- **Pruebas:** agregué un modo demo y un modo foto para probar sin cámara y con distintas caras.

✅ **Resultado**
Un filtro web que abre directo en la cámara, cubre toda la cara, sigue los giros de la cabeza y responde a tres gestos. Me dejó claro cuánto trabajo hay detrás de un filtro "sencillo" de Instagram.

🎥 [video / GIF aquí]
💻 Repositorio: https://github.com/TU-USUARIO/02-filtro-alebrije
🔗 Pruébalo: https://TU-URL

#RealidadAumentada #Blender #MediaPipe #threejs #Oaxaca #Alebrijes #FiltrosAR
