import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='autoemp',
    version='0.1',
    description="A package for uploaing to EMP",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jjjshpmy/empuploader',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'argparse',
        'bs4',
        'configparser',
        'dottorrent-cli',
        'imageio',
        'pathlib',
        'requests',
        'selenium',
        'vcsi'
    ],
    python_requires='==3.7.*',
)