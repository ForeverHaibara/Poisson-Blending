from tkinter import filedialog, Tk, Canvas, Button
from PIL import Image, ImageTk
from blender import PoissonBlending
from utils import * 
import os

class app():
    def __init__(self):
        self.app  = Tk()
        self.w    = 700
        self.h    = 580
        self.step = 1
        self.path = os.path.dirname(__file__)
        
        # widget configuration
        app = self.app
        w   = self.w 
        h   = self.h

        # size of the image box
        w2  = w * 5 / 7
        h2  = h - 150

        app.title("Poisson Image Editting")
        
        self.canvas = Canvas(app, width = w, height = h, bg = "white")



        self.imgs = [0] * 7
        self.tkimgs = [0] * 7
        self.resize = [0] * 7
        
        self.foreground = None
        self.tkforeground = None
        self.foreground_coor = (0, 0)
        self.foreground_resize = (1, 1)
        
        self.imgs[1] = Image.open(self.path + '\\examples\\texture_foreground.png')
        self.imgs[1], self.resize[1] = ResizeKeepAspectRatio(self.imgs[1], w2 * .99, h2 * .99)
        self.tkimgs[1] = ImageTk.PhotoImage(self.imgs[1])
        self.refreshforeground()
    
        self.imgs[3] = Image.open(self.path + '\\examples\\texture_background.png')
        self.imgs[3], self.resize[3] = ResizeKeepAspectRatio(self.imgs[3], w2 * .99, h2 * .99)
        self.tkimgs[3] = ImageTk.PhotoImage(self.imgs[3])

        self.imgs[4] = self.imgs[3]
        self.tkimgs[4] = self.tkimgs[3]


        #self.masklines = []
        #self.mask = None

        self.old_x = -1
        self.old_y = -1
        
        self.btn = Button(app, text = 'Select', 
                                command = self.buttonclick,
                                width = 7, height = 1)
        self.btn.place(x = w - w/7 - 58, y = 67)
        self.redraw()
        
        self.canvas.bind('<B1-Motion>', self.mousemove)
        self.canvas.bind('<ButtonRelease-1>', self.mouserelease)
        self.canvas.bind('<MouseWheel>', self.mousewheel)


    def redraw(self):
        # widget configuration
        app = self.app
        w   = self.w 
        h   = self.h

        # size of the image box
        w2  = w * 5 / 7
        h2  = h - 150

        canvas = self.canvas

        self.trydelete('instruction1')
        self.trydelete('instruction2')
        self.trydelete('line')
        #self.masklines = []

        canvas.create_rectangle(w/7, 100, w - w/7, h-50, outline='blue')

        instructions = (0,'Upload a foreground file.',
                       'Outline the target by circling.',
                       'Upload a background file.',
                       'Place your target on the background. (Drag and scroll!)',
                       'Save your result.')
        canvas.create_text(w/2, 40, text = 'Step %d'%self.step, 
                                font = ('Times New Roman',30), tag = 'instruction1')
        canvas.create_text(w/7 + 115 - self.step%2*15, 82, text = instructions[self.step], 
                                font = ('Times New Roman',15), tag = 'instruction2')
        
        btntexts = ('', 'Select', 'Cancel', 'Select', 'Cancel', 'Save')
        self.btn['text'] = btntexts[self.step]

        self.prev_page = Button(app, text = '<', width = 1, height = 5, command = self.pageprev)
        self.next_page = Button(app, text = '>', width = 1, height = 5, command = self.pagenext)
        self.prev_page.place(x = w/7 - 20, y = h/2 - 50)
        self.next_page.place(x = w - w/7 + 5, y = h/2 - 50)

        self.trydelete('img')
        self.trydelete('img0')
        self.canvas.create_image(w/2, h/2 + 25, image = self.tkimgs[self.step], tag = 'img')
        if self.step == 4:
            self.canvas.create_image(w/2 + self.foreground_coor[0], 
                                    h/2 + 25 + self.foreground_coor[1], 
                                    image = self.tkforeground, tag = 'img0')


    def trydelete(self, x):
        try: self.canvas.delete(x)
        except: pass 


    def buttonclick(self):
        if self.step in (1,3):
           self.openfile()
        elif self.step == 2:
            self.old_x = -1
            self.masklines = []
            self.imgs[2] = self.imgs[1]
            self.tkimgs[2] = self.tkimgs[1]
            #self.redraw()
            #self.app.update()
        elif self.step == 5:
            self.savefile()

        if self.step == 2 or self.step == 4:
            self.old_x = -1
            self.foreground = self.imgs[2].copy()
            self.tkforeground = ImageTk.PhotoImage(self.foreground)
            self.foreground_coor = (0, 0)
            self.foreground_resize = self.resize[1]
            self.redraw()


    def mousemove(self, event):
        canvas = self.canvas 
        if self.step == 2 and self.old_x != -2:
            x , y = event.x , event.y
            w   = self.w 
            h   = self.h

            # the cursor should fall inside the image
            # x = min(max(w/7, x), w - w/7)
            # y = min(max(100, y), h - 50)
            x = min((w + self.resize[1][0])/2, max(x, (w - self.resize[1][0])/2))
            y = min((h + self.resize[1][1])/2 + 25, max(y, (h - self.resize[1][1])/2 + 25))
            
            if self.old_x >= 0:
                canvas.create_line(self.old_x, self.old_y, x, y, width = 3, 
                                    fill = 'black', smooth = True, tag = 'line')
                self.masklines.append([self.old_x, self.old_y])
            else:
                self.masklines = []
            self.old_x , self.old_y = x , y

        elif self.step == 4:
            x , y = event.x , event.y 
            if self.old_x >= 0:
                self.foreground_coor = (
                    self.foreground_coor[0] + x - self.old_x, 
                    self.foreground_coor[1] + y - self.old_y
                )
                self.canvas.move('img0', x - self.old_x, y - self.old_y)

            self.old_x , self.old_y = x , y
            
            
        
    def mouserelease(self, event):
        # print(len(self.masklines))
        self.old_x = -1
        if self.step == 2:
            
            w_bias = (self.w - self.resize[1][0]) / 2
            h_bias = (self.h + 50 - self.resize[1][1]) / 2
            for i in range(len(self.masklines)):
                self.masklines[i] = (self.masklines[i][0] - w_bias,
                                     self.masklines[i][1] - h_bias)

            self.imgs[self.step], self.mask = CutOut(self.imgs[self.step], self.masklines)
            self.tkimgs[self.step] = ImageTk.PhotoImage(self.imgs[self.step])

            self.foreground = self.imgs[self.step].copy()
            self.tkforeground = ImageTk.PhotoImage(self.foreground)
            self.foreground_coor = (0, 0)
            self.foreground_resize = self.resize[1]

            self.redraw()
            self.app.update()


    def mousewheel(self, event):
        # scroll to control the size of the foreground target 
        if self.step == 4:
            if event.delta > 0:
                self.foreground_resize = (int(self.foreground_resize[0] * 1.05) + 1, 
                                            int(self.foreground_resize[1] * 1.05) + 1)
                                            
            else:
                if self.foreground.size[0] > 2 and self.foreground.size[1] > 2:
                    self.foreground_resize = (int(self.foreground_resize[0] * 0.9524), 
                                            int(self.foreground_resize[1] * 0.9524))
                    
            self.foreground = self.imgs[2].resize(self.foreground_resize, Image.ANTIALIAS)            
            self.tkforeground = ImageTk.PhotoImage(self.foreground)

            w = self.w 
            h = self.h
            self.canvas.create_image(w/2 + self.foreground_coor[0], 
                                    h/2 + 25 + self.foreground_coor[1], 
                                    image = self.tkforeground, tag = 'img0')
            self.canvas.pack()
            self.app.update()


    def openfile(self):
        app = self.app
        w   = self.w 
        h   = self.h
        # size of the image box
        w2  = w * 5 / 7
        h2  = h - 150

        try:
            path = filedialog.askopenfilename(initialdir = self.path)
            self.imgs[self.step] = Image.open(path)
        except:
            return 

        self.imgs[self.step], self.resize[self.step] = ResizeKeepAspectRatio(
                                                self.imgs[self.step], w2 * .99, h2 * .99)
        self.tkimgs[self.step] = ImageTk.PhotoImage(self.imgs[self.step])
        
        self.refreshforeground()

        self.canvas.create_image(w/2, h/2 + 25, image = self.tkimgs[self.step], tag = 'img')
        
        self.canvas.pack()
        app.update()


    def savefile(self):
        path = filedialog.asksaveasfilename(initialdir = self.path,
                                            initialfile = 'output.png',
                                            defaultextension='.png',
                                            filetypes=[('image', '.png')])
        if not path.endswith('.png'):
            path = path + '.png'
        self.imgs[5].save(path)


    def refreshforeground(self):        
        self.imgs[self.step + 1] = self.imgs[self.step]
        self.tkimgs[self.step + 1] = self.tkimgs[self.step]
        if self.step == 1:
            self.masklines = []
            self.mask = None
            self.foreground = self.imgs[2].copy()
            self.tkforeground = ImageTk.PhotoImage(self.foreground)
            self.foreground_coor = (0, 0)
            self.foreground_resize = self.resize[1]


    def blending(self):
        # correctly process the foreground to prevent impacts of alpha channel on the image when resizing
        self.correct_foreground = self.imgs[1].copy()
        self.correct_foreground = self.correct_foreground.resize(self.foreground_resize, Image.ANTIALIAS)

        # resize the masklines before rendering IMPORTANT!
        masklines2 = self.masklines[:]
        for i in range(len(self.masklines)):
            masklines2[i] = (
                round(masklines2[i][0] * (self.foreground_resize[1]/self.resize[1][1])),
                round(masklines2[i][1] * (self.foreground_resize[0]/self.resize[1][0]))
            )

        self.correct_foreground, self.correct_mask = CutOut(self.correct_foreground, masklines2)

        # self.correct_foreground = np.array(self.correct_foreground)
        # self.correct_mask = Image.fromarray(self.mask)
        # self.correct_mask = self.correct_mask.resize(self.foreground_resize)
        # self.correct_mask = np.array(self.correct_mask)
        # self.correct_foreground[:,:,-1] = np.where(self.correct_mask > 0, 255, 0)

        # from matplotlib import pyplot as plt 
        # plt.figure(figsize=(15,9))
        # plt.subplot(1,2,1)
        # plt.imshow(self.correct_foreground)
        # plt.subplot(1,2,2)
        # plt.imshow(self.correct_mask)
        # plt.show()

        self.correct_foreground = np.array(self.correct_foreground)
        self.correct_mask = np.array(self.correct_mask)
        return Image.fromarray(PoissonBlending(
                            np.array(self.imgs[4]),
                            self.correct_foreground,
                            np.where(self.correct_mask > 0, 1, 0), # opaque pixels
                            self.resize[3][1]//2 + self.foreground_coor[1] - self.foreground_resize[1]//2,
                            self.resize[3][0]//2 + self.foreground_coor[0] - self.foreground_resize[0]//2                          
                            ))

    def pagenext(self):
        self.old_x = -1
        if self.step == 1:
            pass
            # self.imgs[2] = self.imgs[1]
            # self.tkimgs[2] = self.tkimgs[1]
        elif self.step == 3:
            pass 
            #self.btn.pack_forget()
        elif self.step == 4:
            self.imgs[5] = self.blending()
            self.tkimgs[5] = ImageTk.PhotoImage(self.imgs[5])
        elif self.step == 5:
            return 
        self.step += 1
        self.redraw()
        self.app.update()

    def pageprev(self):
        self.old_x = -1
        if self.step == 1:
            return 
        self.step -= 1
        self.redraw()
        self.app.update()

    def mainloop(self):
        self.canvas.pack()
        self.app.mainloop()


#file = filedialog.askopenfilename(initialdir=os.getcwd())
#print(file)


if __name__ == '__main__':
    app().mainloop()