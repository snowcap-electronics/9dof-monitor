#!/usr/bin/python

import subprocess

SIZE_X     = 1280
SIZE_Y     = 720
WIDTH      = 100
FPS        = 30
STEP       = int(SIZE_X/FPS)
LENGTH     = 60
MAX_X      = SIZE_X - WIDTH
MAX_FRAMES = LENGTH * FPS

direction = 0
x = -STEP

# jitter: Show white and black boxes on top corners for two frames with one frame phase shift between corners
# latency: Show black boxes for 5 seconds and white for 1 second.
mode = "latency"
frame_counter = 0

black_left_box = "-fill black -draw \"rectangle {},4 {},252\"".format(4, 252)
black_right_box = "-fill black -draw \"rectangle {},4 {},252\"".format(SIZE_X - 252, SIZE_X - 4)
white_box = ""

for frame in range(MAX_FRAMES):
    
    if (direction == 0):
        if (x + STEP < MAX_X):
            x += STEP
        else:
            direction = 1
            x -= STEP
    else:
        if (x - STEP >= 0):
            x -= STEP
        else:
            direction = 0
            x += STEP

    x_right_box = SIZE_X - 252
    left_box = white_box
    right_box = white_box

    if mode == "jitter":
        f_counter = frame % 4
        if (f_counter == 0):
            left_box = white_box
            right_box = white_box
        elif (f_counter == 1):
            left_box = white_box
            right_box = black_right_box
        elif (f_counter == 2):
            left_box = black_left_box
            right_box = black_right_box
        elif (f_counter == 3):
            left_box = black_left_box
            right_box = white_box

    elif mode == "latency":
        if frame_counter < 5 * FPS:
            left_box = black_left_box
            right_box = black_right_box
        else:
            left_box = white_box
            right_box = white_box

        frame_counter += 1

        if frame_counter > (5 * FPS + 1 * FPS):
            frame_counter = 0

    # X for the moving white bar
    x2 = x + WIDTH
    # left X for the right white box
    xl = SIZE_X - 256

    convert = "/usr/bin/convert -size {}x{} xc:black -fill white -draw \"rectangle {},0 {},{} rectangle 0,0 256,256 rectangle {},0 {},256\" {} {} jitter_{}.png".format(SIZE_X, SIZE_Y, x, x2, SIZE_Y, xl, SIZE_X, left_box, right_box, str(frame).zfill(5))
    print convert
    subprocess.call(convert, shell=True)
    
ffmpeg = "ffmpeg -framerate {} -y -i jitter_%05d.png -c:v libx264 -profile:v baseline -level 3.0 -preset slow -crf 22 output.mp4".format(FPS)
print ffmpeg
subprocess.call(ffmpeg, shell=True)
