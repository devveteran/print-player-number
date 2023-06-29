import cv2
import numpy as np
import os.path
import math
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))

CHAR_HEIGHT = 400
LETTER_SPACING = 3
CHAR_SPACING = 15

BACK_COLOR = (0, 0, 0, 0)
# BACK_COLOR = (255, 255, 255, 255)

def rotate_image(small_image, angle):
    # Calculate the rotation center point
    # center_x = 0
    # center_y = small_image.shape[0]
    center_x = small_image.shape[1] // 2
    center_y = small_image.shape[0] // 2

    # Obtain the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)

    # Calculate the bounding box of the rotated image
    cos_angle = abs(rotation_matrix[0, 0])
    sin_angle = abs(rotation_matrix[0, 1])
    new_height = int((small_image.shape[1] * sin_angle) + (small_image.shape[0] * cos_angle))
    new_width = int((small_image.shape[1] * cos_angle) + (small_image.shape[0] * sin_angle))

    # Adjust the rotation matrix translation
    rotation_matrix[0, 2] += (new_width / 2) - center_x
    rotation_matrix[1, 2] += (new_height / 2) - center_y

    # Apply the adjusted rotation matrix to the small image
    rotated_image = cv2.warpAffine(small_image, rotation_matrix, (new_width, new_height))
    # cv2.imwrite("rotated_image.png", rotated_image)
    return rotated_image

def merge_image(rotated_image, source_image, x, y):
    rotated_height, rotated_width, _ = rotated_image.shape
    for xi in range(rotated_width):
        for yi in range(rotated_height):
            if (rotated_image[yi, xi] == [0, 0, 0, 0]).all():
                pass
            else:
                source_image[y + yi, x + xi] = rotated_image[yi, xi]
            
    # source_image[y:y + rotated_height, x:x + rotated_width] = rotated_image

def getLetterHeight(imgs, widthLimit, margin):
    ret_height = 1
    while True:
        width_text = 0
        for img in imgs:
            width = img.shape[1]
            height = img.shape[0]
            resized_width = int(width * (ret_height / height))
            width_text += resized_width
        width_text += LETTER_SPACING * (len(imgs) -1)
        if width_text >= widthLimit: # - margin:
            break
        else:
            ret_height += 1
    return ret_height


def warpImage(img, xcent, ycent, wout, hout, backcolor):
    hin, win = img.shape[:2]
    win2 = win / 2

    # specify desired square output dimensions and center
    hwout = max(hout, wout)
    hwout2 = hwout / 2

    map_x = np.zeros((hout, wout), np.float32)
    map_y = np.zeros((hout, wout), np.float32)

    for y in range(hout):
        Y = (y - ycent) * 1
        for x in range(wout):
            X = (x - xcent) * 1
            XX = (math.atan2(Y,X) + math.pi/2) / (math.pi)
            XX = XX * win + win2
            map_x[y, x] = XX
            map_y[y, x] = hwout2 - math.hypot(X,Y)

    result = cv2.remap(img, map_x, map_y, cv2.INTER_CUBIC, borderMode = cv2.BORDER_CONSTANT, borderValue=backcolor)
    return result

def process(name, number, backcolor):
    letter_height = CHAR_HEIGHT

    imgChars = []
    for i in range(len(name)):
        sname = f"./fonts/{name.lower()[i]}.png"
        imgchar = cv2.imread(sname, cv2.IMREAD_UNCHANGED)
        imgChars.append(imgchar)

    max_char_width = 0
    widthText = 0
    for i in range(len(imgChars)):
        imgchar = imgChars[i]
        width = imgchar.shape[1]
        height = imgchar.shape[0]
        image_height = letter_height
        image_width = int(width * (letter_height / height))
        if max_char_width < image_width:
            max_char_width = image_width
        resized_img = cv2.resize(imgchar, (image_width, image_height))
        widthText += image_width
        imgChars[i] = resized_img
        # cv2.imwrite(dir_path + "\\" + str(i) + ".jpg", imgChars[i])

    widthText += (LETTER_SPACING * (len(imgChars) - 1))

    imgDigits = []
    for i in range(len(number)):
        sname = f"./fonts/{number.lower()[i]}.png"
        imgdigit = cv2.imread(sname, cv2.IMREAD_UNCHANGED)
        imgDigits.append(imgdigit)

    digit_height = getLetterHeight(imgDigits, widthText, max_char_width*2)
    # print(digit_height)
    padding_vert = digit_height 
    padding_horz = digit_height

    widthNumber = 0
    for i in range(len(imgDigits)):
        imgdigit = imgDigits[i]
        width = imgdigit.shape[1]
        height = imgdigit.shape[0]
        image_height = digit_height
        image_width = int(width * (digit_height / height))
        resized_img = cv2.resize(imgdigit, (image_width, image_height))

        widthNumber += resized_img.shape[1]
        imgDigits[i] = resized_img
        # cv2.imwrite(dir_path + "\\" + str(i) + ".jpg", resized_img)
    widthNumber += LETTER_SPACING * (len(imgDigits) - 1)

    canvasWidth = widthText + padding_horz * 2
    canvasHeight = digit_height * 2 + padding_vert * 2

    # Get Center of the circle, and the radius
    center_x = int(padding_horz + widthText / 2)
    a = widthText / 2
    b = a // 2
    radius = int((a * a + b * b) / (2 * b))
    center_y = canvasHeight - padding_vert - digit_height

    x_position = int((canvasWidth - widthText) / 2)
    y_position = padding_vert # 0

    imgTemp = np.zeros((canvasHeight, canvasWidth, 4), np.uint8)

    cv2.circle(imgTemp, (center_x, center_y), radius, (255, 0, 0))
    cv2.circle(imgTemp, (center_x, center_y), 10, (0, 0, 255))

    current_angle = 0
    start_angle = -80
    start_y = 0
    while True:
        current_angle = start_angle
        y_position = 0
        for i in range(len(imgChars)):
            angle_radians = np.deg2rad(current_angle)    
            small_image = imgChars[i]
            w = small_image.shape[1]
            h = small_image.shape[0]
            angle_increment = np.rad2deg(2 * np.arcsin((w + CHAR_SPACING) / (2 * radius)))
            x_offset = int(radius * np.sin(angle_radians))
            y_offset = int(radius * np.cos(angle_radians))
            x_position = center_x + x_offset
            y_position = center_y - y_offset
            if i == 0:
                start_y = y_position
            current_angle += angle_increment
        if abs(start_y - y_position) < CHAR_HEIGHT // 3:
            break
        else:
            start_angle += 0.01

    print("start angle = " + str(start_angle))
    angle_offx = 0
    current_angle = start_angle + 0.1
    for i in range(len(imgChars)):
        angle_radians = np.deg2rad(current_angle)

        small_image = imgChars[i]
        w = small_image.shape[1]
        h = small_image.shape[0]
        angle_increment = np.rad2deg(2 * np.arcsin((w + CHAR_SPACING) / (2 * radius)))
        angle_offx += np.rad2deg(2 * np.arcsin((CHAR_SPACING) / (2 * radius)))
        x_offset = int(radius * np.sin(angle_radians))
        y_offset = int(radius * np.cos(angle_radians))

        x_position = center_x + x_offset
        y_position = center_y - y_offset
        cv2.circle(imgTemp, (x_position, y_position), 2, (0, 0, 255))
        rotangle = 360 - current_angle - angle_offx
        rotangle_rad = np.deg2rad(rotangle)
        rotated_image = rotate_image(small_image, rotangle)
        w_rotated = rotated_image.shape[1]
        h_rotated = rotated_image.shape[0]
        offx2 = int(h * np.sin(rotangle_rad))
        offy2 = int(w * np.sin(rotangle_rad))
        if current_angle < 0:
            draw_x = x_position - offx2
            draw_y = y_position - h_rotated
        else:
            draw_x = x_position
            draw_y = y_position - h_rotated - offy2

        merge_image(rotated_image, imgTemp, draw_x, draw_y)
        print("char " + str(i+1) + " printed")
        cv2.circle(imgTemp, (x_position, y_position), 3, (0, 0, 255))
        cv2.circle(imgTemp, (draw_x, draw_y), 3, (0, 0, 255))
        # cv2.imshow("result", imgTemp)
        # cv2.waitKey(0)

        current_angle += angle_increment
    
    #####################
    # for imgchar in imgChars:
    #     merge_image(imgchar, imgTemp, x_position, y_position)
    #     x_position += imgchar.shape[1] + LETTER_SPACING
    # warpedImage = warpImage(imgTemp, center_x, center_y, canvasWidth, canvasHeight, backcolor)
    #####################

    # warpedImage = imgTemp

    x_position = int((canvasWidth - widthNumber) / 2)
    y_position = center_y
    for i in range(len(imgDigits)):
        imgdigit = imgDigits[i]
        merge_image(imgdigit, imgTemp, x_position, y_position)
        print("digit " + str(i+1) + " printed")
        x_position += imgdigit.shape[1] + LETTER_SPACING

    cv2.imwrite(dir_path + "/output.png", imgTemp)
    # cv2.imshow("result", warpedImage)
    # cv2.waitKey(0)

strText=sys.argv[1] if len(sys.argv) > 1 else "nitinsrivastava"
strNumber=sys.argv[2] if len(sys.argv) > 2 else "07"
backColor = BACK_COLOR

process(strText, strNumber, backColor)
