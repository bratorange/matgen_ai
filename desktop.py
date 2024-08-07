import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QProgressBar
from PIL import Image

from InferenceThread import InferenceThread
from LoadModelsThread import LoadModelsThread
from TextureWidget import TextureWidget


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
