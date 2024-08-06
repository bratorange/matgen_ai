import os
import pathlib
import sys

import torch.utils.data
from PIL import Image
from data import create_dataset
from data.aligned_dataset import AlignedDataset
from data.base_dataset import get_params, get_transform
from models import create_model, BaseModel
from options.test_options import TestOptions
from util import util

img_path = pathlib.Path("../samples")
img_name = "clover"

def get_model(map_type: str) -> (BaseModel, TestOptions):
    sys.argv = [
        sys.argv[0],
        "--dataroot", "../../texgen/datasets",
        "--name", "texgen_p2p_Albedo",
        "--model", "pix2pix",
        "--checkpoints_dir", "checkpoints",
        "--batch_size", "2",
        "--load_size", "1024",
        "--crop_size", "1024",
        "--gpu_ids", "-1",
    ]

    opt = TestOptions().parse()  # get test options
    # hard-code some parameters for test
    opt.num_threads = 0  # test code only supports num_threads = 0
    opt.batch_size = 1  # test code only supports batch_size = 1
    opt.serial_batches = True  # disable data shuffling; comment this line if results on randomly chosen images are needed.
    opt.no_flip = True  # no flip; comment this line if results on flipped images are needed.
    opt.display_id = -1  # no visdom display; the test code saves the results to a HTML file.
    opt.name = "texgen_p2p_" + map_type

    # opt.name = "texgen_p2p_Normal"
    # opt.model = "pix2pix"
    # opt.checkpoints_dir = "../ checkpoints"
    # opt.batch_size = 2
    # opt.load_size = 512
    # # opt.crop_size = 512
    # # opt.gpu_ids = -1
    # opt.isTrain = False

    model = create_model(opt)  # create a model given opt.model and other options
    model.setup(opt)  # regular setup: load and print networks; create schedulers
    return model, opt

def infere(model: BaseModel, opt: TestOptions, src_im) -> Image:
    A = src_im
    # apply the same transform to both A and B
    transform_params = get_params(opt, A.size)
    A_transform = get_transform(opt, transform_params, grayscale=False)
    B_transform = A

    A = A_transform(A)
    A = A.unsqueeze(0)
    B = A

    data = {'A': A, 'B': B, 'A_paths': "AB_path", 'B_paths': "AB_path"}

    model.set_input(data)  # unpack data from data loader
    model.test()  # run inference
    visuals = model.get_current_visuals()  # get image results

    items = visuals.items()
    im = util.tensor2im(list(items)[1][1])
    return im


if __name__ == '__main__':
    os.makedirs(img_path / img_name, exist_ok=True)
    names = ["Albedo", "Normal", "Height", "Roughness", "Metallic", ]
    for name in names:
        model, opt = get_model(name)
        im = infere(model, opt, Image.open(img_path / f"{img_name}.jpg").convert('RGB'))
        util.save_image(im, img_path / img_name / f"{img_name}_{name}.png")
