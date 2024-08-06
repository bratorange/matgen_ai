from distutils.core import setup

setup(
    name='pix2pix',
    version='1.0',
    packages=['data', 'util', 'models', 'options'],
    url='',
    license='',
    author='',
    author_email='',
    description='',
    install_requires = [
        "torch>=1.4.0",
        "torchvision>=0.5.0",
        "dominate>=2.4.0",
        "visdom>=0.1.8.8",
        "wandb",
    ],
)