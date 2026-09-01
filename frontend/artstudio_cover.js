import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const COVER_SIZE = 512;
const loader = new GLTFLoader();

function blobFromCanvas(canvas, type = 'image/jpeg', quality = 0.88) {
    return new Promise((resolve, reject) => {
        canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('封面渲染失败。')), type, quality);
    });
}

async function generate(file, options = {}) {
    if (!file) throw new Error('请选择 GLB 模型文件。');
    options.onState?.('cover', 0);
    const objectUrl = URL.createObjectURL(file);
    const canvas = document.createElement('canvas');
    canvas.width = COVER_SIZE;
    canvas.height = COVER_SIZE;
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: true });
    renderer.setPixelRatio(1);
    renderer.setSize(COVER_SIZE, COVER_SIZE, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf3f3f3);
    scene.add(new THREE.HemisphereLight(0xffffff, 0xb8b8b8, 1.8));
    const key = new THREE.DirectionalLight(0xffffff, 2.8);
    key.position.set(4, 7, 6);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 1.2);
    fill.position.set(-4, 3, -5);
    scene.add(fill);

    try {
        const gltf = await loader.loadAsync(objectUrl);
        const model = gltf.scene;
        model.updateMatrixWorld(true);
        const bounds = new THREE.Box3().setFromObject(model);
        if (bounds.isEmpty()) throw new Error('模型没有可渲染的几何体。');

        const center = bounds.getCenter(new THREE.Vector3());
        const size = bounds.getSize(new THREE.Vector3());
        const maxDimension = Math.max(size.x, size.y, size.z, 0.001);
        model.position.sub(center);
        scene.add(model);

        const camera = new THREE.PerspectiveCamera(35, 1, maxDimension / 1000, maxDimension * 1000);
        const distance = (maxDimension / 2) / Math.tan(THREE.MathUtils.degToRad(35) / 2) * 1.28;
        camera.position.set(distance * 0.95, distance * 0.72, distance * 0.95);
        camera.lookAt(0, 0, 0);
        renderer.render(scene, camera);
        options.onState?.('cover', 100);
        return await blobFromCanvas(canvas);
    } finally {
        URL.revokeObjectURL(objectUrl);
        renderer.dispose();
        scene.traverse(node => {
            if (!node.isMesh) return;
            node.geometry?.dispose?.();
            const materials = Array.isArray(node.material) ? node.material : [node.material];
            materials.forEach(material => material?.dispose?.());
        });
    }
}

window.OntoTwinAssetCover = { generate, COVER_SIZE };
