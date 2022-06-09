from PIL import Image, ImageDraw
import numpy as np 

def ResizeKeepAspectRatio(img, x, y):
    """Resize an image with anti-aliasing flag and keeped aspect ratio."""
    w2, h2 = img.size # width and height
    if y / h2 < x / w2:
        s = (y / h2 * w2, y)
    else:
        s = (x, x / w2 * h2)

    s = (int(s[0]), int(s[1]))
    return img.resize(s, Image.ANTIALIAS), s


def CutOut(img, lines):
    """Cutout an img by a sequence of lines. The parameter 'lines' is a list of vertices."""

    mask = np.full((img.size[1], img.size[0]), 255, dtype = 'uint8')
    mask = Image.fromarray(mask)

    mask = RenderMask(mask, lines)
    mask = np.array(mask)

    img = img.convert('RGBA')

    img = np.array(img)
    img[:,:,-1] = np.where(mask > 0, 255, 0)
    img = Image.fromarray(img)

    # from matplotlib import pyplot as plt 
    # plt.imshow(img)
    # plt.show()
    # return boolean 2darray mask
    return img, mask


def RenderMask(img, lines):
    """Render the mask of the image given a sequence of lines."""
    if len(lines) > 0:
        w , h = img.size 
        w , h = w - 1, h - 1

        lines.append(lines[0])
        draw = ImageDraw.Draw(img)
        for v1, v2 in zip(lines[:-1], lines[1:]):
            draw.line((min(w,max(v1[0],0)), 
                       min(h,max(v1[1],0)),
                       min(w,max(v2[0],0)),
                       min(h,max(v2[1],0))), 
                       fill = 127, width = 3)

        for i in range(h+1):
            ImageDraw.floodfill(img, (0, i), 0)
            ImageDraw.floodfill(img, (w, i), 0)

        for i in range(w+1):
            ImageDraw.floodfill(img, (i, 0), 0)
            ImageDraw.floodfill(img, (i, h), 0)

        # from matplotlib import pyplot as plt 
        # plt.imshow(img)
        # plt.show()

    return img 