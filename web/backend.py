import base64
import io
import queue
import sys
import uuid
from threading import Thread, Lock

from PIL import Image
from data.base_dataset import get_params, get_transform
from flask import Flask, request, jsonify, send_from_directory
from models import create_model, BaseModel
from options.test_options import TestOptions
from util import util

app = Flask(__name__, static_folder='frontend/static', static_url_path='')

job_queue = queue.Queue()
job_results = {}
job_lock = Lock()
job_progress = {}

def get_model(map_type: str):
    sys.argv = [
        sys.argv[0],
        "--dataroot", "../../texgen/datasets",
        "--name", f"texgen_p2p_{map_type}",
        "--model", "pix2pix",
        "--checkpoints_dir", "checkpoints",
        "--batch_size", "2",
        "--load_size", "1024",
        "--crop_size", "1024",
        "--gpu_ids", "-1",
    ]

    opt = TestOptions().parse()
    opt.num_threads = 0
    opt.batch_size = 1
    opt.serial_batches = True
    opt.no_flip = True
    opt.display_id = -1

    model = create_model(opt)
    model.setup(opt)
    return model, opt


def infere(model: BaseModel, opt: TestOptions, src_im):
    A = src_im
    transform_params = get_params(opt, A.size)
    A_transform = get_transform(opt, transform_params, grayscale=False)
    B_transform = A

    A = A_transform(A)
    A = A.unsqueeze(0)
    B = A

    data = {'A': A, 'B': B, 'A_paths': "AB_path", 'B_paths': "AB_path"}

    model.set_input(data)
    model.test()
    visuals = model.get_current_visuals()

    items = visuals.items()
    im = util.tensor2im(list(items)[1][1])
    return im

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(app.static_folder, 'styles.css')


@app.route('/script.js')
def serve_js():
    return send_from_directory(app.static_folder, 'script.js')

def inference_worker():
    while True:
        job_id, image = job_queue.get()
        if job_id is None:
            break

        results = {}
        for i, (name, model) in enumerate(models.items()):
            im = infere(model, model.opt, image)
            pil_image = Image.fromarray(im)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            results[name] = encoded_image

            # Update progress
            with job_lock:
                job_progress[job_id] = (i + 1) / len(models) * 100

        with job_lock:
            job_results[job_id] = results
            job_progress[job_id] = 100

        job_queue.task_done()


# Modify the upload_image function
@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files['image']
    img = Image.open(io.BytesIO(image.read())).convert('RGB')
    job_id = str(uuid.uuid4())

    with job_lock:
        job_progress[job_id] = 0

    job_queue.put((job_id, img))

    return jsonify({"job_id": job_id}), 202


# Modify the get_job_status function
@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    with job_lock:
        if job_id in job_results:
            progress = job_progress.pop(job_id, 100)
            return jsonify({"status": "completed", "progress": progress, "result": job_results[job_id]}), 200
        elif job_id in job_progress:
            return jsonify({"status": "processing", "progress": job_progress[job_id]}), 200

    queue_position = [job[0] for job in list(job_queue.queue)].index(job_id) if job_id in [job[0] for job in list(
        job_queue.queue)] else -1
    if queue_position != -1:
        return jsonify({"status": "waiting", "queue_position": queue_position}), 200

    return jsonify({"status": "not found"}), 404


# Add a new route to cancel a job
@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    with job_lock:
        if job_id in job_progress:
            del job_progress[job_id]
        if job_id in job_results:
            del job_results[job_id]

    # Remove the job from the queue if it's still there
    job_queue.queue = queue.Queue([job for job in list(job_queue.queue) if job[0] != job_id])

    return jsonify({"status": "cancelled"}), 200


if __name__ == '__main__':
    # Load all models
    models = {}
    for name in ["Albedo", "Normal", "Height", "Roughness", "Metallic"]:
        models[name], _ = get_model(name)
    inference_thread = Thread(target=inference_worker, daemon=True)
    inference_thread.start()

    try:
        app.run(port=8000, debug=True)
    finally:
        job_queue.put((None, None))
        inference_thread.join()
