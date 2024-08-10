let currentJobId = null;
let scene, camera, renderer, cube, controls;
let textures = {};
let isDragging = false;


function initThreeJS() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    camera = new THREE.PerspectiveCamera(75, 4/6, 0.1, 50);
    camera.position.z = 2;

    renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('preview-canvas'), antialias: true });
    renderer.setSize(400, 600);

    // Create a subdivided cube geometry
    const geometry = new THREE.BoxGeometry(1, 1, 1, 128, 128, 128);
    const material = new THREE.MeshPhongMaterial({
        color: 0x156289,
        side: THREE.DoubleSide,
        flatShading: true
    });
    cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

    // Lights
    const lights = [];
    lights[0] = new THREE.DirectionalLight(0xffffff, 3);
    lights[1] = new THREE.DirectionalLight(0xffffff, 3);
    lights[2] = new THREE.DirectionalLight(0xffffff, 3);

    lights[0].position.set(0, 200, 0);
    lights[1].position.set(100, 200, 100);
    lights[2].position.set(-100, -200, -100);

    scene.add(lights[0]);
    scene.add(lights[1]);
    scene.add(lights[2]);

    // Add OrbitControls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controls.screenSpacePanning = false;
    controls.maxPolarAngle = Math.PI / 2;
    controls.enableZoom = false; // Disable zooming

    animate();

    window.addEventListener('resize', onWindowResize, false);
}

function animate() {
    requestAnimationFrame(animate);

    controls.update();
    renderer.render(scene, camera);
}
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function updatePreview(results) {
    const textureLoader = new THREE.TextureLoader();

    for (const [mapType, imageData] of Object.entries(results)) {
        const texture = textureLoader.load('data:image/png;base64,' + imageData);
        textures[mapType] = texture;
    }

    applyTextures();
}

function onMouseDown(event) {
    isDragging = true;
    controls.enabled = true;
}

function onMouseUp(event) {
    isDragging = false;
    controls.enabled = false;
}

function onMouseMove(event) {
    if (isDragging) {
        controls.update();
    }
}

function uploadImage() {
    const input = document.getElementById('imageInput');
    const file = input.files[0];
    if (!file) {
        alert('Please select a file first!');
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        currentJobId = data.job_id;
        showOverlay();
        checkStatus(data.job_id);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function checkStatus(jobId) {
    fetch(`/api/status/${jobId}`)
    .then(response => response.json())
    .then(data => {
        updateOverlay(data);
        if (data.status === 'completed') {
            displayResults(data.result);
            hideOverlay();
        } else {
            setTimeout(() => checkStatus(jobId), 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateOverlay(data) {
    const overlayStatus = document.getElementById('overlay-status');
    const progressBar = document.getElementById('progress');

    if (data.status === 'processing') {
        overlayStatus.textContent = 'Processing...';
        progressBar.style.width = `${data.progress}%`;
    } else if (data.status === 'waiting') {
        overlayStatus.textContent = 'Waiting for resources to become available...';
        progressBar.style.width = '0%';
    }
}

function showOverlay() {
    document.getElementById('overlay').style.display = 'block';
}

function hideOverlay() {
    document.getElementById('overlay').style.display = 'none';
}

function cancelJob() {
    if (currentJobId) {
        fetch(`/api/cancel/${currentJobId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            hideOverlay();
            currentJobId = null;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

function displayResults(results) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '';

    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.bottom = '10px';
    container.style.left = '10px';
    container.style.display = 'flex';
    container.style.flexWrap = 'wrap';
    container.style.justifyContent = 'flex-start';
    container.style.maxWidth = '380px'; // Adjust based on your preview size

    for (const [mapType, imageData] of Object.entries(results)) {
        const imgContainer = document.createElement('div');
        imgContainer.className = 'texture-container';

        const img = document.createElement('img');
        img.src = `data:image/png;base64,${imageData}`;
        img.alt = `${mapType} Map`;
        img.className = 'texture-preview';
        img.dataset.type = mapType;
        img.addEventListener('click', toggleTexture);

        const label = document.createElement('p');
        label.textContent = `${mapType}`;
        label.style.fontSize = '12px';
        label.style.margin = '2px 0';

        imgContainer.appendChild(img);
        imgContainer.appendChild(label);
        container.appendChild(imgContainer);
    }

    resultDiv.appendChild(container);

    updatePreview(results);
}

function applyTextures() {
    if (textures.Albedo) cube.material.map = textures.Albedo;
    if (textures.Normal) cube.material.normalMap = textures.Normal;
    if (textures.Height) {
        cube.material.displacementMap = textures.Height;
        cube.material.displacementScale = 0.05;
    }
    if (textures.Roughness) cube.material.roughnessMap = textures.Roughness;
    if (textures.Metallic) cube.material.metalnessMap = textures.Metallic;

    cube.material.needsUpdate = true;
}

function toggleTexture(event) {
    const img = event.target;
    const mapType = img.dataset.type;

    img.classList.toggle('disabled');

    if (img.classList.contains('disabled')) {
        cube.material[getTextureProperty(mapType)] = null;
    } else {
        cube.material[getTextureProperty(mapType)] = textures[mapType];
    }

    cube.material.needsUpdate = true;
}

function getTextureProperty(mapType) {
    switch (mapType) {
        case 'Albedo': return 'map';
        case 'Normal': return 'normalMap';
        case 'Height': return 'displacementMap';
        case 'Roughness': return 'roughnessMap';
        case 'Metallic': return 'metalnessMap';
        default: return '';
    }
}

window.addEventListener('beforeunload', function (e) {
    if (currentJobId) {
        cancelJob();
    }
});

initThreeJS();
