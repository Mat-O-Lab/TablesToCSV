import os
import cv2
import numpy as np
from pdf2image import convert_from_path
import pathlib
import os.path

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image, ImageOps


def converter(img):
    """
    converts the input (image)
    output only consists of the combination of the vertical and horizontal lines
    """
    # thresholding the image to a binary image
    thresh, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # inverting the image
    img_bin = 255 - img_bin

    # countcol(width) of kernel as 50th of total width
    kernel_len = np.array(img).shape[1] // 50
    # Defining a vertical kernel to detect all vertical lines of image
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    # Defining a horizontal kernel to detect all horizontal lines of image
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    # A kernel of 2x2
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

    # Use vertical kernel to detect and save the vertical lines in a jpg
    image_1 = cv2.erode(img_bin, ver_kernel, iterations=3)
    vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=3)
    # Use horizontal kernel to detect and save the horizontal lines in a jpg
    image_2 = cv2.erode(img_bin, hor_kernel, iterations=3)
    horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=3)

    # Combine horizontal and vertical lines in a new third image, with both having same weight.
    img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
    # Eroding and thesholding the image
    img_vh = cv2.erode(~img_vh, kernel, iterations=2)
    thresh, img_vh = cv2.threshold(img_vh, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # plotting = plt.imshow(img_vh,cmap='gray')
    # plt.show()
    return img_vh, vertical_lines, horizontal_lines


def imageCrop(img_vh):
    """
    using the function tableseperator to crop the image
    """
    img_vh = Image.fromarray(img_vh)
    img_vh_invert = ImageOps.invert(img_vh)

    w, h = img_vh.size
    # Seperator for Whitespace (Table)

    transpose = False
    verticalSpikes = tableSeperator(img_vh_invert, transpose)
    # print(verticalSpikes)
    croppedList = []
    for (y_start, y_end) in verticalSpikes:
        croppedList.append((img_vh_invert.crop((0, y_start, w, y_end)), (y_start, y_end)))

    transpose = True
    horizontalCroppedList = []
    for (image, (y_start, y_end)) in croppedList:
        horizontalSpikes = tableSeperator(image, transpose)
        w_cI, h_cI = image.size
        # print(horizontalSpikes)
        if len(horizontalSpikes) > 1:
            for (x_start, x_end) in horizontalSpikes:
                if (x_end - x_start > 50 and y_end - y_start > 50):
                    image_new = image.crop((x_start, 0, x_end, h_cI))
                    # image_new.show()
                    verticalSpikes = tableSeperator(image_new, transpose=False)
                    for (y_start_new, y_end_new) in verticalSpikes:
                        horizontalCroppedList.append((image.crop((x_start, y_start_new, x_end, y_end_new)),
                                                      (x_start, (y_start + y_start_new), x_end, (y_end + y_start_new))))
        else:
            for (x_start, x_end) in horizontalSpikes:
                if (x_end - x_start > 50 and y_end - y_start > 50):
                    horizontalCroppedList.append(
                        (image.crop((x_start, 0, x_end, h_cI)), (x_start, y_start, x_end, y_end)))

    return horizontalCroppedList


def tableSeperator(img, transpose):
    """
    detects where vertical/horizontal lines are and give the coordinates of them back
    """
    image_array = np.array(img)
    width, height = img.size

    if (transpose):
        image_array = image_array.T
        var = width
    else:
        var = height

    spikes = []
    startSpikeDetected = False
    start = 0
    end = 0
    for row in range(var):
        # detecting the start of a spike
        if (sum(image_array[row][:]) != 0 and startSpikeDetected != True):
            start = row
            startSpikeDetected = True
        # detecting the end of a spike and save the start&end of the spike
        elif (sum(image_array[row][:]) == 0 and startSpikeDetected) or (row == var - 1 and startSpikeDetected):
            startSpikeDetected = False
            end = row - 1
            spikes.append((start, end))

    return spikes


def detect_graphs(oriCroppedImgs, originalImg):
    """
    sort out graphs that got recognized as tables
    """
    for (ori_image_crop, image_crop, bounding_box) in oriCroppedImgs:
        oriImg = originalImg.crop(bounding_box)
        conv_crop, vertical_lines, horizontal_lines = converter(np.array(oriImg))

        horizontal_lines = Image.fromarray(horizontal_lines)
        vertical_lines = Image.fromarray(vertical_lines)
        vertical_spikes = tableSeperator(vertical_lines, True)
        horizontal_spikes = tableSeperator(horizontal_lines, False)

        cells = (len(vertical_spikes) + 1) * (len(horizontal_spikes) + 1)
        w, h = ori_image_crop.size
        table_size = w * h
        if (table_size / cells) > 25000:
            oriCroppedImgs.remove((ori_image_crop, image_crop, bounding_box))


def main(filename):

    filename = filename.replace(".pdf", "")

    pages = convert_from_path(filename + ".pdf", poppler_path="poppler-21.11.0/Library/bin", dpi=200)
    values = []
    for page, i in zip(pages, range(len(pages))):
        oriCroppedImgs = []
        croppedImages = []

        filename = filename + '_page_' + str(i)
        # print(filename)

        page.save('temp/' + filename + '.png', 'png')

        img = cv2.imread('temp/' + filename + '.png', 0)
        originalImg = Image.fromarray(img)
        # originalImg.show()

        img_vh, vertical_lines, horizontal_lines = converter(img)

        w, h = originalImg.size

        croppedImages += imageCrop(img_vh)

        for (image, bounding_box) in croppedImages:

            (x_start, y_start, x_end, y_end) = bounding_box

            # Abfrage ob eines der oriCroppedImages zu groß ist, falls ja alles nochmal ab converter mit den ori images
            if (x_end - x_start > w - 200 and y_end - y_start > h - 200):
                croppedImages2 = []
                oriImg = originalImg.crop((x_start + 6, y_start + 6, x_end - 6, y_end - 6))

                open_cv_image = np.array(oriImg)

                img_vh, vertical_lines, horizontal_lines = converter(open_cv_image)
                croppedImages2 += imageCrop(img_vh)

                for (image, bounding_box) in croppedImages2:
                    (x_start_crop, y_start_crop, x_end_crop, y_end_crop) = bounding_box
                    bounding_box2 = (
                    x_start_crop + x_start + 6, y_start_crop + y_start + 6, x_end_crop + (w - x_end) + 6,
                    y_end_crop + (y_start) + 6)
                    oriCroppedImgs.append((oriImg.crop(bounding_box), image, bounding_box2))

            else:
                oriCroppedImgs.append((originalImg.crop(bounding_box), image, bounding_box))

        detect_graphs(oriCroppedImgs, originalImg)

        w, h = originalImg.size
        for (ori_image_crop, image_crop, bounding_box) in oriCroppedImgs:
            bounding_box = [bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]]
            values.append([i + 1, bounding_box, [w, h]])

    # delete files that are not needed anymore
    for path in pathlib.Path("temp").iterdir():
        os.remove(path)

    return values