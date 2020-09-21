# autoemp

## Prerequisites
Requires Python 3.7  
Requires Google Chrome

## Virtual environment
- Create a virtual environment through conda
    ```
    conda create --name autoemp python=3.7
    ```

- Activate the virtual environment
    ```
    conda activate autoemp
    ```

## Installation
- Clone the repo and cd into it:
    ```
    git clone https://github.com/jjjshpmy/empuploader.git
    cd empuploader
    ```
- Install autoemp package
    ```
    pip install -e .
    ```

- Install chromedriver
    ```
    chmod +x install_chromedrver.sh
    ./install_chromedriver.sh
    ```

## Uploading videos
First create or fill out media.cfg. The default location looks for the file in the media folder. Video information and screenshots will be automatically entered into the description. An example template is shown below. See https://docs.python.org/3/library/configparser.html#supported-ini-file-structure for more details.
```
[<filename.extension>]
Title : <title of video>
Tags : <tag 1> <tag 2> ... <tag n>
Category : <category>
Description : <anything you want>
    <to put in the description>
    <goes in here>
    
    <indent multi lines and empty lines>
    <contact sheet will be filled automatically>

[<filename2.extension>]
Title : <title of second video>
Tags : <some> <more> ... <tags>
Category : <another category>
Description : <a short>
    <description>
    <goes here>
```

To run the package
```
python -m autoemp.run --media /path/to/folder
```

To view different options
```
python -m autoemp.run -h
```
