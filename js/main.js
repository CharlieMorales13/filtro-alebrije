import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';
import { initAudio, sfx } from './audio.js';
import { Disparador, blendshape } from './gestos.js';

const VISION = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm';
const MODELO_CARA = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';
const PARAMS = new URLSearchParams(location.search);
const DEMO = PARAMS.has('demo');
const IMAGEN = PARAMS.get('imagen'); // ?imagen=foto.jpg: prueba con una foto en lugar de la cámara
const SUAVIZADO = 0.65; // 1 = sin suavizado; menor = menos temblor pero más retraso

// Tintes que se alternan al subir las cejas (multiplican la textura de la máscara).
const TINTES = [0xffffff, 0xff9ec7, 0x8ff5ea, 0xffe066, 0xc9a7ff];
const CONFETI = [0xf21a73, 0x00b3a6, 0xffc700, 0xff5a00, 0x5acc26, 0x7326bf];

const $ = id => document.getElementById(id);
let fuente = $('video'); // <video> de la cámara, o <img> en modo ?imagen
const estado = $('estado');

// ---------- three.js ----------
const renderer = new THREE.WebGLRenderer({ canvas: $('lienzo'), alpha: true, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
// Misma cámara que usa MediaPipe para la matriz facial: FOV vertical de 63°, unidades en cm.
const camera = new THREE.PerspectiveCamera(63, 1, 1, 10000);
scene.add(new THREE.HemisphereLight(0xffffff, 0x332244, 2.2));
const luz = new THREE.DirectionalLight(0xffffff, 1.5);
luz.position.set(0, 30, 60);
scene.add(luz);

const cara = new THREE.Group();   // sigue la matriz facial
cara.matrixAutoUpdate = false;
cara.visible = false;
scene.add(cara);
const mascara = new THREE.Group(); // escala para el "pulso" del rugido
cara.add(mascara);

let mixer = null;
let piel = null;
let tinte = 0;
let pulso = 0;
let destello = 0;
const particulas = [];
const reloj = new THREE.Clock();

new GLTFLoader().load('assets/mascara_zorro.glb', gltf => {
  mascara.add(gltf.scene);
  gltf.scene.traverse(o => {
    if (o.material?.name === 'piel') piel = o.material;
  });
  piel?.emissive.setHex(0xffc700);
  mixer = new THREE.AnimationMixer(gltf.scene);
  gltf.animations.forEach(clip => mixer.clipAction(clip).play());
});

// ---------- gestos ----------
const disparadores = {
  boca: new Disparador(0.5, 0.3, 800),
  cejas: new Disparador(0.55, 0.3, 1200),
  ojos: new Disparador(0.6, 0.3, 1000),
};

const REACCIONES = {
  boca() { // rugido: confeti desde la boca + pulso
    pulso = 1;
    emitir(new THREE.Vector3(0, -6, 9), 90, CONFETI, 50);
    sfx('rugido');
  },
  cejas() { // cambia los colores de la máscara
    tinte = (tinte + 1) % TINTES.length;
    piel?.color.setHex(TINTES[tinte]);
    emitir(new THREE.Vector3(0, 12, 4), 30, [TINTES[tinte] === 0xffffff ? 0xffc700 : TINTES[tinte]], 25);
    sfx('colores');
  },
  ojos() { // la máscara destella en dorado y salen chispas de los ojos
    destello = 1;
    emitir(new THREE.Vector3(-3.2, 2.6, 7), 15, [0xffffff, 0xffc700], 20);
    emitir(new THREE.Vector3(3.2, 2.6, 7), 15, [0xffffff, 0xffc700], 20);
    sfx('brillo');
  },
};

function disparar(nombre) {
  REACCIONES[nombre]();
  const chip = document.querySelector(`[data-gesto="${nombre}"]`);
  chip.classList.add('activo');
  setTimeout(() => chip.classList.remove('activo'), 600);
}

function revisarGestos(categorias, ahora) {
  const valores = {
    boca: blendshape(categorias, 'jawOpen'),
    cejas: blendshape(categorias, 'browInnerUp'),
    ojos: Math.min(blendshape(categorias, 'eyeBlinkLeft'), blendshape(categorias, 'eyeBlinkRight')),
  };
  for (const [nombre, d] of Object.entries(disparadores)) {
    if (d.actualizar(valores[nombre], ahora)) disparar(nombre);
  }
}

// ---------- partículas (en espacio de la cara, en cm) ----------
function emitir(origen, n, colores, fuerza) {
  for (let i = 0; i < n; i++) {
    const p = new THREE.Mesh(
      new THREE.PlaneGeometry(1.8, 1.2),
      new THREE.MeshBasicMaterial({ color: colores[i % colores.length], side: THREE.DoubleSide, transparent: true }),
    );
    p.position.copy(origen);
    p.userData.v = new THREE.Vector3((Math.random() - 0.5) * fuerza, (Math.random() - 0.3) * fuerza, Math.random() * fuerza * 0.8 + 10);
    p.userData.vida = 1.4;
    cara.add(p);
    particulas.push(p);
  }
}

function actualizarParticulas(dt) {
  for (let i = particulas.length - 1; i >= 0; i--) {
    const p = particulas[i];
    p.userData.v.y -= 40 * dt;
    p.position.addScaledVector(p.userData.v, dt);
    p.rotation.x += 9 * dt;
    p.rotation.z += 6 * dt;
    p.userData.vida -= dt;
    p.material.opacity = Math.min(1, p.userData.vida * 2);
    if (p.userData.vida <= 0) {
      cara.remove(p);
      p.geometry.dispose();
      p.material.dispose();
      particulas.splice(i, 1);
    }
  }
}

// ---------- seguimiento suavizado ----------
const objetivo = { pos: new THREE.Vector3(), rot: new THREE.Quaternion(), esc: new THREE.Vector3() };
const actual = { pos: new THREE.Vector3(), rot: new THREE.Quaternion(), esc: new THREE.Vector3(1, 1, 1) };
let primerCuadro = true;

function seguir(matriz) {
  matriz.decompose(objetivo.pos, objetivo.rot, objetivo.esc);
  const a = primerCuadro ? 1 : SUAVIZADO;
  primerCuadro = false;
  actual.pos.lerp(objetivo.pos, a);
  actual.rot.slerp(objetivo.rot, a);
  actual.esc.lerp(objetivo.esc, a);
  cara.matrix.compose(actual.pos, actual.rot, actual.esc);
  cara.matrixWorldNeedsUpdate = true;
}

// ---------- bucle ----------
function animar(dt) {
  mixer?.update(dt);
  pulso = Math.max(0, pulso - dt * 2.5);
  mascara.scale.setScalar(1 + 0.12 * Math.sin(pulso * Math.PI));
  destello = Math.max(0, destello - dt * 1.5);
  if (piel) piel.emissiveIntensity = destello * 0.6;
  actualizarParticulas(dt);
  renderer.render(scene, camera);
}

let landmarker = null;
let ultimoTiempo = -1;

function cuadro() {
  const dt = Math.min(reloj.getDelta(), 0.1);
  if (landmarker && fuenteNueva()) {
    const ahora = performance.now();
    const r = landmarker.detectForVideo(fuente, ahora);
    if (r.facialTransformationMatrixes?.length) {
      cara.visible = true;
      seguir(new THREE.Matrix4().fromArray(r.facialTransformationMatrixes[0].data));
      revisarGestos(r.faceBlendshapes[0].categories, ahora);
      estado.textContent = '';
    } else {
      cara.visible = false;
      primerCuadro = true;
      estado.textContent = 'Muestra tu cara a la cámara';
    }
  }
  animar(dt);
}

function fuenteNueva() {
  if (!(fuente instanceof HTMLVideoElement)) return true;
  if (fuente.readyState < 2 || fuente.currentTime === ultimoTiempo) return false;
  ultimoTiempo = fuente.currentTime;
  return true;
}

function ajustarTamano() {
  const w = fuente.videoWidth || fuente.naturalWidth || innerWidth;
  const h = fuente.videoHeight || fuente.naturalHeight || innerHeight;
  renderer.setSize(w, h, false); // el CSS (object-fit: cover) recorta igual que al video
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

async function crearLandmarker() {
  const fileset = await FilesetResolver.forVisionTasks(VISION);
  const opciones = delegate => ({
    baseOptions: { modelAssetPath: MODELO_CARA, delegate },
    runningMode: 'VIDEO',
    numFaces: 1,
    outputFaceBlendshapes: true,
    outputFacialTransformationMatrixes: true,
  });
  try {
    return await FaceLandmarker.createFromOptions(fileset, opciones('GPU'));
  } catch {
    return await FaceLandmarker.createFromOptions(fileset, opciones('CPU'));
  }
}

async function iniciar() {
  // abre directo al filtro: pide la cámara frontal al cargar
  try {
    if (IMAGEN) {
      const img = new Image();
      img.src = IMAGEN;
      await img.decode();
      img.id = 'video';
      fuente.replaceWith(img);
      fuente = img;
    } else {
      fuente.srcObject = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      await fuente.play();
    }
  } catch (err) {
    estado.innerHTML = 'No se pudo abrir la cámara frontal.<br><small>Da permiso de cámara y abre la página con HTTPS.</small>';
    console.error(err);
    return;
  }
  ajustarTamano();
  fuente.addEventListener('resize', ajustarTamano);
  estado.textContent = 'Cargando detector facial…';
  landmarker = await crearLandmarker();
  estado.textContent = 'Muestra tu cara a la cámara';
  renderer.setAnimationLoop(cuadro);
}

// Modo demo (?demo): sin cámara, la máscara gira frente a la cámara virtual.
// Teclas 1, 2, 3 o window.simular('boca' | 'cejas' | 'ojos') para probar reacciones.
function iniciarDemo() {
  scene.background = new THREE.Color(0x2a1b3d);
  estado.textContent = '';
  ajustarTamano();
  cara.visible = true;
  window.simular = disparar;
  addEventListener('keydown', e => {
    const gesto = { 1: 'boca', 2: 'cejas', 3: 'ojos' }[e.key];
    if (gesto) disparar(gesto);
  });
  renderer.setAnimationLoop(() => {
    const t = reloj.elapsedTime;
    const m = new THREE.Matrix4().makeTranslation(0, 0, -60)
      .multiply(new THREE.Matrix4().makeRotationY(Math.sin(t * 0.8) * 0.6))
      .multiply(new THREE.Matrix4().makeRotationX(Math.sin(t * 0.5) * 0.15));
    seguir(m);
    animar(Math.min(reloj.getDelta(), 0.1));
  });
}

// el audio necesita un toque del usuario
const btnSonido = $('sonido');
addEventListener('pointerdown', async () => {
  await initAudio();
  btnSonido.classList.add('oculto');
  btnSonido.remove();
}, { once: true });

if (DEMO) iniciarDemo();
else iniciar();
