import datetime
import os
import re
import sys
from os import listdir
from os.path import isfile, join
from pathlib import Path

from PIL import Image, ImageFont, ImageDraw, ExifTags

fill = (250, 123, 9)

def get_font(image, txt):
    fontsize = 1  # starting font size

    # portion of image width you want text width to be
    img_fraction = 0.2

    font = ImageFont.truetype("fonts/digital-7 (mono italic).ttf", fontsize)
    max_dim = max(image.size)
    while font.getsize(txt)[0] < img_fraction * max_dim:
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype("fonts/digital-7 (mono italic).ttf", fontsize)

    return font

def get_orientation(img):
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == "Orientation":
            break
    exif = dict(img._getexif().items())
    # 1 correct, no need
    orientation_value = exif[orientation] if orientation in exif else -1
    return orientation_value

def get_coords(img, is_vertical, orientation_value, text_width):
    width, height = img.size
    width_offset = width * (0.05 if is_vertical else 0.2)
    height_offset = height * (0.2 if is_vertical else 0.05)

    if orientation_value == 3:
        left_offset = width - width_offset
        top_offset = height_offset
    elif orientation_value == 6:
        left_offset = width - width_offset
        top_offset = height - height_offset
    elif orientation_value == 8:
        left_offset = width_offset
        top_offset = height_offset
    else:
        left_offset = width_offset
        top_offset = height - height_offset

    return left_offset, top_offset


def get_draw_image(image, text):
    is_vertical_img = is_vertical(image)

    orientation_value = get_orientation(image)
    print(orientation_value)

    font = get_font(image, text)
    coords = get_coords(image, is_vertical_img, orientation_value, font.getsize(text)[0])

    width, height = image.size
    max_dim = max(width, height)

    mask_size = (max_dim * 2, max_dim * 2)
    mask = Image.new('L', mask_size, 0)

    draw = ImageDraw.Draw(mask)
    draw.text((max_dim, max_dim), text, 255, font=font)

    rotated_mask = mask.rotate(180 if orientation_value == 3 else 180 if orientation_value == 6 else 90 if is_vertical_img else 0)

    # crop the mask to match image
    mask_xy = (max_dim - coords[0], max_dim - coords[1])
    b_box = mask_xy + (mask_xy[0] + width, mask_xy[1] + height)
    mask = rotated_mask.crop(b_box)

    color_image = Image.new('RGBA', image.size, fill)
    image.paste(color_image, mask)
    return image


def is_vertical(image):
    width, height = image.size
    return width < height

def get_time_watermark(image):
    file_name = Path(image.filename).stem
    # if file name is time format, then directly use it
    reg_result = re.findall(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}", file_name)
    time_in_file = reg_result[0] if len(reg_result) > 0 else None

    if time_in_file is None:

        _exif = image._getexif()
        if _exif != None and 36867 in _exif:
            creation_date = _exif[36867]
            try:
                time_watermark = datetime.datetime.strptime(creation_date, "%Y:%m:%d %H:%M:%S").strftime(
                    "%Y-%m-%d %H:%M:%S")
            except:
                create_date_found = re.findall(r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", creation_date)[0]
                time_watermark = datetime.datetime.strptime(create_date_found, "%Y:%m:%d %H:%M:%S").strftime(
                    "%Y-%m-%d %H:%M:%S")
        else:
            # use file name as watermark
            time_watermark = file_name
    else:
        time_watermark = datetime.datetime.strptime(time_in_file, "%Y_%m_%d_%H_%M_%S").strftime(
            "%Y-%m-%d %H:%M:%S")

    return time_watermark

def add_time_mark(src_file, dest_file, index):
    print(index, "Adding time watermark for ", src_file)
    image = Image.open(src_file)

    time_watermark = get_time_watermark(image)
    # add watermark
    image = get_draw_image(image, time_watermark)

    info = image.info
    image.save(dest_file, quality=95, **info)
    # print(index, "Added time watermark and saved in ", src_file)


if __name__ == '__main__':

    src_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/henry/Downloads/src"
    dest_dir = os.path.join(src_dir, "output")
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
        print("Output folder is created: ", dest_dir)

    files = [f for f in listdir(src_dir) if isfile(join(src_dir, f)) and f.split(".")[1] != "HEIC"]
    index = 0
    for file in listdir(src_dir):
        if isfile(join(src_dir, file)) and not file.startswith("."):
            index += 1
            src_file = join(src_dir, file)
            dest_file = join(dest_dir, file)
            add_time_mark(src_file, dest_file, index)

    print("Finally processed", index, " images!")
