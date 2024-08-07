import sys

from PyQt5.QtCore import QThread, pyqtSignal
from models import create_model
from options.test_options import TestOptions


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
