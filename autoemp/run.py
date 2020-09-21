'''
main.py

Auto uploader for EMP

Only works for single video files. All files must be in the top level directory
specified in the config.

Usage:
    python -m autoemp.run --media <media_path>
'''

import argparse
from bs4 import BeautifulSoup
import configparser
import imageio
import json
import os
from pathlib import Path
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import shutil
import subprocess


def parse_args_config():
    # Construct the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments to the parser
    parser.add_argument('--media', type=Path, required=True,
        help='path to media folder')
    parser.add_argument('--config', type=Path,
        default=Path(__file__).parent.joinpath('autoemp.cfg'),
        help='path to autoemp config file')
    parser.add_argument('--media_config', type=Path, 
        help='path to media config file')
    parser.add_argument('--rename', action='store_true',
        help='rename files')
    parser.add_argument('--safe', action='store_true',
        help='enable safe mode (e.g. no overwriting files, no skip dupe check)')

    args = parser.parse_args()
    args.media_config = args.media_config or args.media.joinpath('media.cfg')

    # Construct the config parser
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(args.config)
    media_config = configparser.ConfigParser()
    media_config.read(args.media_config)

    return args, config, media_config


def find_media_filenames(media_path, media_types):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(media_path):
        f.extend(filenames)
        break

    r = re.compile('^.*\.({})$'.format('|'.join(media_types)), re.IGNORECASE)
    return filter(r.match, f)


def generate_folder(file, file_config, media_path, rename, safe):
    # Find out filename
    if 'Title' not in file_config:
        file_config['Title'] = Path(file).with_suffix('')

    # Create new directory
    file_dir = media_path.joinpath(file_config['Title'])
    file_dir.mkdir(exist_ok=not safe)

    # Move file
    new_path = file_dir.joinpath(file_config['Title']+Path(file).suffix) \
        if rename else file_dir.joinpath(file)
    shutil.move(media_path.joinpath(file), new_path)

    return new_path


def generate_images(path, config, file_config):
    # Generate contact sheet
    output = subprocess.run(['vcsi', path, '-t', '-O', path.with_suffix(''),
        # grid
        '-g', f"{config['columns']}x{config['rows']}", 
        # width with gap between images
        '-w', str(config.getint('columns')*(config.getint('tile_width')+10)), 
        '--verbose'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    
    # Get video details
    output = output.splitlines()
    file_config['extension'] = Path(output[2]).suffix[1:]
    file_config['file size'] = output[6]
    file_config['duration'] = output[5]
    file_config['resolution'] = output[3]

    # Generate gif
    images = []
    for filename in path.with_suffix('').iterdir():
        images.append(imageio.imread(filename))
    imageio.mimsave(str(path)+'.gif', images, duration=.5)

    # Delete thumbnail folder
    shutil.rmtree(path.with_suffix(''), ignore_errors=True)

    return Path(str(path)+'.jpg'), Path(str(path)+'.gif')


def upload_image(img_path, cover):
    with requests.Session() as s:
        # Upload image
        r = s.post('https://fapping.empornium.sx/upload.php',
                   files=dict(ImageUp=open(img_path, 'rb')))
        if r.status_code != 200:
            raise Exception('Error occurred during image upload')

        # Get link
        image = json.loads(r.text)['image_id_public']
        image = 'https://fapping.empornium.sx/image/'+image

        soup = requests.get(image)
        soup = BeautifulSoup(soup.text, 'html.parser')
        soup = soup.find('div',
            {'class' :'image-tools-section show_directly'})
        soups = soup.find_all('div',{'class' :'input-item'})
        for soup in soups:
            if (cover and 'Direct link' in soup.label.text) or (
                not cover and 'BBCode' in soup.label.text):
                return (soup.input['value'])

        raise Exception(f'Could not find link at {image}')


def login(user_config, site_config):
    # Set up connection
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)

    # Log in
    driver.get(site_config['LOGIN_URL'])

    driver.find_element_by_name('username').send_keys(user_config['username'])

    driver.find_element_by_name('password').send_keys(user_config['password'])

    keeploggedin_box = driver.find_element_by_id('keeploggedin')
    if not keeploggedin_box.is_selected():
        keeploggedin_box.click()

    driver.find_element_by_name('submit').click()

    # Get announce url
    if 'announce_url' not in user_config:
        driver.get(site_config['UPLOAD_URL'])
        url = driver.find_element_by_xpath(site_config['ANNOUNCE_XPATH'])
        user_config['announce_url'] = url.get_property('value')

    return driver


def create_torrent(file, announce_url, output):
    subprocess.run(['dottorrent', '-p', '-t', announce_url, '-s', '8M', file,
        output])
    return Path(str(file)+'.torrent')


def upload_torrent(driver, file, file_config, site_config, safe):
    driver.get(site_config['UPLOAD_URL'])

    # Check for dupe
    file_input = driver.find_element_by_name('file_input')
    file_input.send_keys(str(file.resolve()))
    driver.find_element_by_name('checkonly').click()
    if 'dupe' in driver.find_element_by_id('messagebar').text:
        if safe:
            raise Exception(f'Dupe detected for {file.resolve()}')
        else:
            # TODO test this
            ignore_dupes = driver.find_element_by_name('ignoredupes')
            if not ignore_dupes.is_selected():
                ignore_dupes.click()
    
    # Fill in information
    select = Select(driver.find_element_by_id('category'))
    select.select_by_visible_text(file_config['Category'])
    title = driver.find_element_by_name('title')
    title.clear()
    title.send_keys(file_config['Title'])
    driver.find_element_by_id('taginput').send_keys(file_config['Tags'])
    driver.find_element_by_name('image').send_keys(file_config['Cover image'])
    description = driver.find_element_by_name('desc')
    description.send_keys(file_config['Description'], '\n')
    description.send_keys('[info]\n', f"Format : {file_config['extension']}\n",
        f"File size : {file_config['file size']}\n",
        f"Length : {file_config['duration']}\n",
        f"Resolution : {file_config['resolution']}\n")
    description.send_keys('[screens]\n', file_config['Contact sheet'])

    driver.find_element_by_id('post').click()


def main():
    # Parse args and configs
    args, config, media_config = parse_args_config()

    # Find valid videos
    files = find_media_filenames(args.media, list(config['Media Types']))
    
    for file in files:
        if file not in media_config:
            raise Exception(f'No config found for {file}')

        # Create output directory
        file_path = generate_folder(file, media_config[file], args.media,
            args.rename, args.safe)

        # Generate contact sheet and gif
        cs_path, gif_path = generate_images(file_path, config['Contact Sheet'],
            media_config[file])

        # Upload images
        cs_link = upload_image(cs_path, cover=False)
        gif_link = upload_image(gif_path, cover=True)
        media_config[file]['Contact sheet'] = cs_link
        media_config[file]['Cover image'] = gif_link

        # Login to EMP
        driver = login(config['User'], config['Site'])

        # Create torrent
        torrent_path = create_torrent(file_path.parent,
            config['User']['announce_url'], args.media)
        
        
        # Upload torrent
        upload_torrent(driver, torrent_path, media_config[file], config['Site'],
            args.safe)


if __name__ == '__main__':
    main()
