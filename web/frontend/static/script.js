let currentJobId = null;
let scene, camera, renderer, cube;
let textures = {};
let isDragging = false;
let previousMousePosition = {
    x: 0,
    y: 0
};

function initThreeJS() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    camera = new THREE.PerspectiveCamera(75, 1, 0.1, 50);
    camera.position.z = 2;

    renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('preview-canvas'), antialias: true });
    renderer.setSize(400, 400);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1;
    renderer.outputEncoding = THREE.sRGBEncoding;

    const geometry = new THREE.SphereGeometry(1, 128, 64);
    const material = new THREE.MeshStandardMaterial({
        side: THREE.DoubleSide,
    });
    cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

    const lights = [];
    lights[0] = new THREE.DirectionalLight(0xffffff, .5);
    lights[1] = new THREE.DirectionalLight(0xffffff, 1);
    lights[2] = new THREE.DirectionalLight(0xffffff, 1);

    lights[0].position.set(0, 200, 0);
    lights[1].position.set(100, 200, 100);
    lights[2].position.set(-100, -200, -100);

    scene.add(lights[0]);
    scene.add(lights[1]);
    scene.add(lights[2]);

    animate();

    renderer.domElement.addEventListener('mousedown', onMouseDown, false);
    renderer.domElement.addEventListener('mousemove', onMouseMove, false);
    renderer.domElement.addEventListener('mouseup', onMouseUp, false);
}

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

function onMouseDown(event) {
    isDragging = true;
    previousMousePosition = {
        x: event.clientX,
        y: event.clientY
    };
}

function onMouseUp(event) {
    isDragging = false;
}

function onMouseMove(event) {
    if (!isDragging) return;

    const deltaMove = {
        x: event.clientX - previousMousePosition.x,
        y: event.clientY - previousMousePosition.y
    };

    const rotationSpeed = 0.005;

    cube.rotation.y += deltaMove.x * rotationSpeed;
    cube.rotation.x += deltaMove.y * rotationSpeed;

    previousMousePosition = {
        x: event.clientX,
        y: event.clientY
    };
}

function updatePreview(results) {
    const textureLoader = new THREE.TextureLoader();

    for (const [mapType, imageData] of Object.entries(results)) {
        const texture = textureLoader.load('data:image/png;base64,' + imageData);
        textures[mapType] = texture;
    }

    applyTextures();
}

function initUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('imageInput');
    const uploadedImage = document.getElementById('uploaded-image');
    const dragDropArea = document.getElementById('drag-drop-area');
    const uploadLabel = document.getElementById('upload-label');
    const clearButton = document.getElementById('clear-image');

    const cachedImageSrc = localStorage.getItem('cachedImage');
    if (cachedImageSrc) {
        uploadedImage.src = cachedImageSrc;
        uploadedImage.style.display = 'block';
        dragDropArea.style.display = 'none';
        clearButton.style.display = 'block';
        deactivateUploadAreaBorder();
    }

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#0063c1';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.removeProperty('border-color');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.removeProperty('border-color');
        imageInput.files = e.dataTransfer.files;
        handleFileSelect({ target: imageInput });
    });

    imageInput.addEventListener('change', handleFileSelect);
    clearButton.addEventListener('click', clearImage);
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const uploadedImage = document.getElementById('uploaded-image');
            const dragDropArea = document.getElementById('drag-drop-area');
            const clearButton = document.getElementById('clear-image');

            uploadedImage.src = e.target.result;
            uploadedImage.style.display = 'block';
            dragDropArea.style.display = 'none';
            clearButton.style.display = 'block';
            deactivateUploadAreaBorder();

            localStorage.setItem('cachedImage', e.target.result);
        };
        reader.readAsDataURL(file);
    }
    updateButtonStates();
}

function clearImage() {
    const uploadedImage = document.getElementById('uploaded-image');
    const dragDropArea = document.getElementById('drag-drop-area');
    const clearButton = document.getElementById('clear-image');
    const imageInput = document.getElementById('imageInput');

    uploadedImage.src = '';
    uploadedImage.style.display = 'none';
    dragDropArea.style.display = 'block';
    clearButton.style.display = 'none';
    imageInput.value = '';

    localStorage.removeItem('cachedImage');

    activateUploadAreaBorder();
    updateButtonStates();
}

function activateUploadAreaBorder() {
    const uploadArea = document.getElementById('upload-area');
    uploadArea.classList.remove('has-image');
}

function deactivateUploadAreaBorder() {
    const uploadArea = document.getElementById('upload-area');
    uploadArea.classList.add('has-image');
}

function updateButtonStates() {
    const uploadButton = document.getElementById('upload-button');
    const saveTexturesButton = document.getElementById('save-textures-button');
    const imageInput = document.getElementById('imageInput');

    uploadButton.disabled = !imageInput.files.length;
    saveTexturesButton.disabled = !Object.keys(textures).length;

    updateButtonStyle(uploadButton);
    updateButtonStyle(saveTexturesButton);
}

function updateButtonStyle(button) {
    if (button.disabled) {
        button.style.opacity = '0.5';
        button.style.cursor = 'not-allowed';
    } else {
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
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
        if(data.error) {
            alert(data.error);
            return;
        }
        currentJobId = data.job_id;
        showOverlay();
        checkStatus(data.job_id);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while uploading the image.');
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
        alert('An error occurred while checking the job status.');
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
            alert('An error occurred while canceling the job.');
        });
    }
}

function saveTextures() {
    if (!Object.keys(textures).length) {
        alert('No textures to save. Please upload and process an image first.');
        return;
    }

    showOverlay();
    document.getElementById('overlay-status').textContent = 'Preparing textures for download...';
    document.getElementById('progress').style.width = '0%';

    const zip = new JSZip();

    let processedTextures = 0;
    const totalTextures = Object.keys(textures).length;

    for (const [mapType, texture] of Object.entries(textures)) {
        const canvas = document.createElement('canvas');
        canvas.width = texture.image.width;
        canvas.height = texture.image.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(texture.image, 0, 0);

        const imageData = canvas.toDataURL('image/png').split(',')[1];
        zip.file(`${mapType}.png`, imageData, {base64: true});

        processedTextures++;
        const progress = (processedTextures / totalTextures) * 100;
        document.getElementById('progress').style.width = `${progress}%`;
    }

    zip.generateAsync({type:"blob"})
    .then(function(content) {
        hideOverlay();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(content);
        link.download = 'textures.zip';
        link.click();
    })
    .catch(function(error) {
        hideOverlay();
        console.error('Error generating zip file:', error);
        alert('An error occurred while preparing the textures for download.');
    });
}

function displayResults(results) {
    updatePreview(results);

    const textureControls = document.getElementById('texture-controls');
    const texturePreviews = textureControls.getElementsByClassName('texture-preview');

    for (const [mapType, imageData] of Object.entries(results)) {
        const img = textureControls.querySelector(`[data-type="${mapType}"]`);
        if (img) {
            img.src = `data:image/png;base64,${imageData}`;
            img.classList.remove('placeholder');
            img.classList.add('active');
        }
    }

    updateButtonStates();
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

function initTexturePreviews() {
    const textureControls = document.getElementById('texture-controls');
    const mapTypes = ["Albedo", "Normal", "Height", "Roughness", "Metallic"];

    mapTypes.forEach(mapType => {
        const imgContainer = document.createElement('div');
        imgContainer.className = 'texture-container';

        const img = document.createElement('img');
        img.className = 'texture-preview placeholder';
        img.dataset.type = mapType;
        img.addEventListener('click', toggleTexture);

        const label = document.createElement('p');
        label.textContent = mapType;
        label.style.fontSize = '12px';
        label.style.color = '#fff';

        imgContainer.appendChild(img);
        imgContainer.appendChild(label);
        textureControls.appendChild(imgContainer);
    });
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

document.addEventListener('DOMContentLoaded', function() {
    initThreeJS();
    initTexturePreviews();
    initUploadArea();
    updateButtonStates();
});
