import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader";

function Body() {
  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f5);

    // Camera - Isometric
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 1000);
    camera.position.set(8, 8, 8); // Isometric angle
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    canvasRef.current.appendChild(renderer.domElement);

    // Responsive sizing
    const updateSize = () => {
      if (!canvasRef.current) return;
      const width = canvasRef.current.clientWidth;
      const height = canvasRef.current.clientHeight;

      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    updateSize();
    window.addEventListener("resize", updateSize);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 20, 10);
    scene.add(directionalLight);

    // Load model
    let trainModel: THREE.Object3D | null = null;
    const loader = new GLTFLoader();
    loader.load(
      "/assets/TrainOnTrack.glb",
      (gltf) => {
        trainModel = gltf.scene;
        trainModel.scale.set(3, 3, 3);

        const box = new THREE.Box3().setFromObject(trainModel);
        const center = box.getCenter(new THREE.Vector3());
        trainModel.position.sub(center);

        scene.add(trainModel);
      },
      undefined,
      (error) => {
        console.error(error);
        const geometry = new THREE.BoxGeometry(2, 1, 4);
        const material = new THREE.MeshLambertMaterial({ color: 0x4f46e5 });
        trainModel = new THREE.Mesh(geometry, material);
        scene.add(trainModel);
      }
    );

    // Auto-rotation & horizontal drag
    let autoRotate = true;
    let isDragging = false;
    let targetRotationY = 0;
    let currentRotationY = 0;
    let lastMouseX = 0;

    const onMouseMove = (event: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = event.clientX - lastMouseX;
      targetRotationY += deltaX * 0.01; // rotate only Y-axis
      lastMouseX = event.clientX;
      autoRotate = false;
    };

    const onMouseDown = (event: MouseEvent) => {
      isDragging = true;
      lastMouseX = event.clientX;
      autoRotate = false;
    };

    const onMouseUp = () => {
      isDragging = false;
      setTimeout(() => (autoRotate = true), 2000);
    };

    canvasRef.current.addEventListener("mousemove", onMouseMove);
    canvasRef.current.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mouseup", onMouseUp);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      if (trainModel) {
        if (autoRotate && !isDragging) targetRotationY += 0.005;
        currentRotationY += (targetRotationY - currentRotationY) * 0.1;
        trainModel.rotation.y = currentRotationY;
      }
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      window.removeEventListener("resize", updateSize);
      window.removeEventListener("mouseup", onMouseUp);
      if (canvasRef.current) {
        canvasRef.current.removeEventListener("mousemove", onMouseMove);
        canvasRef.current.removeEventListener("mousedown", onMouseDown);
      }
      renderer.dispose();
      if (canvasRef.current && renderer.domElement) {
        canvasRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <div className="flex-1 flex flex-col justify-center items-start p-8 min-w-0">
        <h1 className="text-5xl font-bold text-gray-800 mb-6 leading-tight">
          Welcome to the Train.....
        </h1>
        <p className="text-gray-600 text-xl leading-relaxed max-w-lg">
          Explore your train's stats.
        </p>
        <div className="mt-8 flex gap-4">
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
            Learn More
          </button>
          <button className="border border-gray-300 hover:border-gray-400 text-gray-700 px-6 py-3 rounded-lg font-medium transition-colors">
            Sign up
          </button>
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div ref={canvasRef} className="w-full h-full" />
      </div>
    </div>
  );
}

export default Body;
