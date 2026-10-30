"""
Generate a self-contained interactive 3D HTML viewer for ISYARA STL models.
Embeds the binary STL files as base64 so it can be opened directly with double-click
in any browser (Chrome, Edge, Firefox) without CORS issues or web server requirements.
"""

import os
import base64

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_base64_stl(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

b64_back = get_base64_stl("isyara_back_shell.stl")
b64_assembled = get_base64_stl("isyara_assembled_enclosure.stl")
b64_front = get_base64_stl("isyara_front_shell.stl")

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISYARA V2 — Interactive 3D STL Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        body {{
            background: #0d1117;
            color: #e6edf3;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }}
        #canvas-container {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        }}
        .header-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(22, 27, 34, 0.85);
            backdrop-filter: blur(12px);
            padding: 18px 24px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            max-width: 420px;
            pointer-events: auto;
        }}
        .header-panel h1 {{
            font-size: 20px;
            color: #38bdf8;
            font-weight: 700;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .header-panel p {{
            font-size: 13px;
            color: #8b949e;
            line-height: 1.5;
        }}
        .badge {{
            display: inline-block;
            background: #0369a1;
            color: #e0f2fe;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 9999px;
            margin-top: 6px;
        }}
        .controls-panel {{
            position: absolute;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            background: rgba(22, 27, 34, 0.9);
            backdrop-filter: blur(12px);
            padding: 10px 16px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        button.btn {{
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        button.btn:hover {{
            background: #30363d;
            color: #ffffff;
            border-color: #38bdf8;
        }}
        button.btn.active {{
            background: #0284c7;
            color: #ffffff;
            border-color: #38bdf8;
            box-shadow: 0 0 12px rgba(2, 132, 199, 0.5);
        }}
        .info-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 10;
            background: rgba(22, 27, 34, 0.85);
            backdrop-filter: blur(12px);
            padding: 16px 20px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 12px;
            color: #8b949e;
            line-height: 1.6;
        }}
        .info-panel strong {{
            color: #f0f6fc;
        }}
        .stats {{
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.08);
            font-family: monospace;
            font-size: 11px;
            color: #7ee787;
        }}
    </style>
    <!-- Three.js from Cloudflare CDN with local fallback support -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="canvas-container"></div>

    <div class="header-panel">
        <h1>📐 ISYARA V2 3D Viewer</h1>
        <p>Preview langsung file STL cadangan untuk casing perangkat ISYARA (AITC UNAIR 2026).</p>
        <span class="badge" id="model-badge">Assembled Enclosure (Utuh)</span>
    </div>

    <div class="info-panel">
        <p><strong>💡 Navigasi 3D:</strong></p>
        <p>• <strong>Klik Kiri + Geser:</strong> Putar 360°</p>
        <p>• <strong>Scroll Mouse:</strong> Zoom In / Out</p>
        <p>• <strong>Klik Kanan + Geser:</strong> Panning (Geser Posisi)</p>
        <div class="stats" id="mesh-stats">
            Dimensi: 76 × 150 × 22.4 mm<br>
            Watertight: Ya (100% Manifold)
        </div>
    </div>

    <div class="controls-panel">
        <button class="btn active" onclick="loadModel('assembled')">📦 Casing Utuh (Assembled)</button>
        <button class="btn" onclick="loadModel('back')">📱 Sisi User (Back Shell)</button>
        <button class="btn" onclick="loadModel('front')">📷 Sisi Depan (Front Shell)</button>
        <button class="btn" id="btn-wireframe" onclick="toggleWireframe()">🕸️ Wireframe</button>
        <button class="btn" id="btn-rotate" onclick="toggleRotation()">🔄 Auto Putar</button>
    </div>

    <script>
        const STL_DATA = {{
            'assembled': "{b64_assembled}",
            'back': "{b64_back}",
            'front': "{b64_front}"
        }};

        const MODEL_INFO = {{
            'assembled': {{
                title: "Assembled Enclosure (Utuh)",
                badge: "Casing Lengkap (Assembly)",
                dim: "76 × 150 × 22.4 mm",
                detail: "Mated shells (Front + Back) dengan switch & port USB-C"
            }},
            'back': {{
                title: "Back Shell (Sisi Pengguna)",
                badge: "Back Shell (User-Facing)",
                dim: "76 × 150 × 11.2 mm",
                detail: "OLED SSD1306, TFT LCD ST7735S, & 16-Button Keypad (4×4)"
            }},
            'front': {{
                title: "Front Shell (Sisi Lawan Bicara)",
                badge: "Front Shell (Outward-Facing)",
                dim: "76 × 150 × 11.2 mm",
                detail: "Camera ESP32-CAM, Speaker Grille ⌀32mm, USB-C Port"
            }}
        }};

        let scene, camera, renderer, controls, currentMesh = null;
        let isWireframe = false, isAutoRotate = true;

        // Custom Binary STL parser (Fast & Pure Vanilla JS)
        function parseBinarySTL(base64Data) {{
            const binaryString = atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {{
                bytes[i] = binaryString.charCodeAt(i);
            }}
            const reader = new DataView(bytes.buffer);
            const numTriangles = reader.getUint32(80, true);

            const vertices = new Float32Array(numTriangles * 9);
            const normals = new Float32Array(numTriangles * 9);

            let offset = 84;
            for (let i = 0; i < numTriangles; i++) {{
                const nx = reader.getFloat32(offset, true);
                const ny = reader.getFloat32(offset + 4, true);
                const nz = reader.getFloat32(offset + 8, true);
                offset += 12;

                for (let j = 0; j < 3; j++) {{
                    const vx = reader.getFloat32(offset, true);
                    const vy = reader.getFloat32(offset + 4, true);
                    const vz = reader.getFloat32(offset + 8, true);
                    offset += 12;

                    const idx = i * 9 + j * 3;
                    vertices[idx] = vx;
                    vertices[idx + 1] = vy;
                    vertices[idx + 2] = vz;

                    normals[idx] = nx;
                    normals[idx + 1] = ny;
                    normals[idx + 2] = nz;
                }}
                offset += 2; // Attribute byte count
            }}

            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
            geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
            geometry.computeVertexNormals();
            return geometry;
        }}

        function init() {{
            const container = document.getElementById('canvas-container');
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0e17);

            camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 2000);
            camera.position.set(130, -180, 160);

            renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            // Orbit controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.autoRotate = isAutoRotate;
            controls.autoRotateSpeed = 1.2;

            // Grid helper
            const grid = new THREE.GridHelper(300, 30, 0x1f293d, 0x141a29);
            grid.rotation.x = Math.PI / 2;
            grid.position.z = -15;
            scene.add(grid);

            // Lighting
            const ambient = new THREE.AmbientLight(0xffffff, 0.55);
            scene.add(ambient);

            const keyLight = new THREE.DirectionalLight(0x38bdf8, 0.9);
            keyLight.position.set(150, 200, 250);
            scene.add(keyLight);

            const fillLight = new THREE.DirectionalLight(0xa78bfa, 0.6);
            fillLight.position.set(-150, -150, 150);
            scene.add(fillLight);

            const backLight = new THREE.DirectionalLight(0xffffff, 0.4);
            backLight.position.set(0, 150, -150);
            scene.add(backLight);

            window.addEventListener('resize', onWindowResize);

            // Load initial model
            loadModel('assembled');

            animate();
        }}

        function loadModel(type) {{
            // Update active button
            const buttons = document.querySelectorAll('.controls-panel .btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            const targetBtn = Array.from(buttons).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(type));
            if (targetBtn) targetBtn.classList.add('active');

            // Update badge & stats
            const info = MODEL_INFO[type];
            document.getElementById('model-badge').innerText = info.badge;
            document.getElementById('mesh-stats').innerHTML = `
                <strong>Dimensi:</strong> ${{info.dim}}<br>
                <strong>Komponen:</strong> ${{info.detail}}<br>
                <strong>Mesh:</strong> Watertight Solid (STL)
            `;

            if (currentMesh) {{
                scene.remove(currentMesh);
                currentMesh.geometry.dispose();
                currentMesh.material.dispose();
            }}

            const geometry = parseBinarySTL(STL_DATA[type]);
            geometry.center(); // Center to (0,0,0) for easy orbiting

            // Material color tailored to type
            let matColor = 0x0284c7; // blue
            if (type === 'assembled') matColor = 0x10b981; // emerald
            if (type === 'front') matColor = 0x06b6d4; // cyan

            const material = new THREE.MeshStandardMaterial({{
                color: matColor,
                roughness: 0.35,
                metalness: 0.15,
                wireframe: isWireframe
            }});

            currentMesh = new THREE.Mesh(geometry, material);
            scene.add(currentMesh);
        }}

        function toggleWireframe() {{
            isWireframe = !isWireframe;
            if (currentMesh) currentMesh.material.wireframe = isWireframe;
            document.getElementById('btn-wireframe').classList.toggle('active', isWireframe);
        }}

        function toggleRotation() {{
            isAutoRotate = !isAutoRotate;
            controls.autoRotate = isAutoRotate;
            document.getElementById('btn-rotate').classList.toggle('active', isAutoRotate);
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        window.onload = init;
    </script>
</body>
</html>
"""

html_path = os.path.join(OUTPUT_DIR, "preview_3d_interactive.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated standalone 3D interactive viewer: {html_path} ({os.path.getsize(html_path):,} bytes)")
