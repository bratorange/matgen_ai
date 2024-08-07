from OpenGL.GL import glGenTextures, glTexImage2D
from OpenGL.raw.GL.ARB.internalformat_query2 import GL_TEXTURE_2D
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_RGB, glTexParameteri, GL_TEXTURE_MIN_FILTER, GL_LINEAR, \
    GL_TEXTURE_MAG_FILTER
from OpenGL.raw.GL.VERSION.GL_1_1 import glBindTexture
from OpenGL.raw.GL._types import GL_UNSIGNED_BYTE
from PyQt5.QtCore import QThread, pyqtSignal
from data.base_dataset import get_params, get_transform
from util import util


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
