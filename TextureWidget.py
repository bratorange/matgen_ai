import sys

from OpenGL.GL import *
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QProgressBar
from data.base_dataset import get_params, get_transform
from models import create_model
from options.test_options import TestOptions
from util import util


class LoadModelsThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def run(self):
        model_names = ['Albedo', 'Height', 'Metallic', 'Normal', 'Roughness']
        models = {}
        for i, name in enumerate(model_names):
            sys.argv = [
                sys.argv[0],
                "--dataroot", "../../texgen/datasets",
                "--name", f"texgen_p2p_{name}",
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
            opt.name = f"texgen_p2p_{name}"

            model = create_model(opt)
            model.setup(opt)
            models[name] = (model, opt)
            self.progress.emit((i + 1) * 20)  # 20% progress per model
        self.finished.emit(models)

class InferenceThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, models, img):
        super().__init__()
        self.models = models
        self.img = img

    def run(self):
        results = {}
        for i, (name, (model, opt)) in enumerate(self.models.items()):
            transform_params = get_params(opt, self.img.size)
            A_transform = get_transform(opt, transform_params, grayscale=False)
            A = A_transform(self.img)
            A = A.unsqueeze(0)

            data = {'A': A, 'B': A, 'A_paths': "AB_path", 'B_paths': "AB_path"}
            model.set_input(data)
            model.test()
            visuals = model.get_current_visuals()
            output = util.tensor2im(list(visuals.items())[1][1])
            results[name] = output
            self.progress.emit((i + 1) * 20)  # 20% progress per model
        self.finished.emit(results)

class TextureWidget(QGLWidget):
    def __init__(self, parent=None):
        super(TextureWidget, self).__init__(parent)
        self.textures = {}

    def initializeGL(self):
        glEnable(GL_TEXTURE_2D)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        if not self.textures:
            return

        width = self.width() // 3
        height = self.height() // 2

        for i, (name, texture_id) in enumerate(self.textures.items()):
            x = (i % 3) * width
            y = (i // 3) * height

            glViewport(x, y, width, height)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, 1, 0, 1, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            glBindTexture(GL_TEXTURE_2D, texture_id)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(0, 0)
            glTexCoord2f(1, 0); glVertex2f(1, 0)
            glTexCoord2f(1, 1); glVertex2f(1, 1)
            glTexCoord2f(0, 1); glVertex2f(0, 1)
            glEnd()

            # Render texture name
            glColor3f(1, 1, 1)
            self.renderText(width // 10, height // 10, name)

    def set_textures(self, textures):
        self.textures.clear()
        for name, img_data in textures.items():
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_data.shape[1], img_data.shape[0], 0,
                         GL_RGB, GL_UNSIGNED_BYTE, img_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            self.textures[name] = texture_id
        self.updateGL()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Texture Generator")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.texture_widget = TextureWidget()
        layout.addWidget(self.texture_widget)

        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        layout.addWidget(self.load_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.models = None
        self.load_models()

    def load_models(self):
        self.load_thread = LoadModelsThread()
        self.load_thread.progress.connect(self.update_progress)
        self.load_thread.finished.connect(self.on_models_loaded)
        self.load_thread.start()

    def on_models_loaded(self, models):
        self.models = models
        self.progress_bar.setValue(0)
        self.load_button.setEnabled(True)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            img = Image.open(file_name).convert('RGB')
            img = img.resize((1024, 1024))

            self.inference_thread = InferenceThread(self.models, img)
            self.inference_thread.progress.connect(self.update_progress)
            self.inference_thread.finished.connect(self.on_inference_finished)
            self.inference_thread.start()

    def on_inference_finished(self, results):
        self.texture_widget.set_textures(results)
        self.progress_bar.setValue(0)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
