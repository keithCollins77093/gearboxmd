#   Source:     https://stackoverflow.com/questions/7960600/python-tkinter-display-animated-gif-using-pil
#
#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         view/AnimatedLabel.py
#   Date Started:   September 5, 2022
#   Purpose:        Animation for gears graphics.
#   Development:
#

from tkinter import *
from PIL import Image, ImageTk


from model.Util import IMAGE_DEFAULT_MOVING


class MyLabel(Label):
    def __init__(self, master, filename):
        im = Image.open(filename)
        seq =  []
        try:
            while 1:
                seq.append(im.copy())
                im.seek(len(seq)) # skip to next frame
        except EOFError:
            pass # we're done

        try:
            self.delay = im.info['duration']
        except KeyError:
            self.delay = 100

        first = seq[0].convert('RGBA')
        self.frames = [ImageTk.PhotoImage(first)]

        Label.__init__(self, master, image=self.frames[0])

        temp = seq[0]
        for image in seq[1:]:
            temp.paste(image)
            frame = temp.convert('RGBA')
            self.frames.append(ImageTk.PhotoImage(frame))

        self.idx = 0

        self.cancel = self.after(self.delay, self.play)

    def play(self):
        self.config(image=self.frames[self.idx])
        self.idx += 1
        if self.idx == len(self.frames):
            self.idx = 0
        self.cancel = self.after(self.delay, self.play)


root = Tk()
anim = MyLabel(root, IMAGE_DEFAULT_MOVING)
anim.pack()

def stop_it():
    anim.after_cancel(anim.cancel)

Button(root, text='stop', command=stop_it).pack()

root.mainloop()