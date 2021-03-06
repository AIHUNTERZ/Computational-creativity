import tarfile
import threading
import tkinter
import tkinter as tk
from tkinter.messagebox import showerror
import os

import PIL
import tensorflow as tf
from tkinter import filedialog
import tensorflow_hub as hub
import numpy as np
from threading import Thread
from concurrent.futures import Future
from PIL import Image
from PIL import ImageTk as itk
import requests

# Load compressed models from tensorflow_hub
os.environ['TFHUB_MODEL_LOAD_FORMAT'] = 'COMPRESSED'


def call_with_future(fn, future, args, kwargs):
    try:
        result = fn(*args, **kwargs)
        future.set_result(result)
    except Exception as exc:
        future.set_exception(exc)


def threaded(fn):
    def wrapper(*args, **kwargs):
        future = Future()
        Thread(target=call_with_future, args=(fn, future, args, kwargs)).start()
        return future
    return wrapper


class AST(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, highlightbackground="blue", highlightthickness=1)
        self.image_file = ''
        self.style_file = ''
        self.result = None
        self.hub_model = None
        self.open_file_path = os.path.dirname(os.path.abspath(__file__))
        self.open_style_path = os.path.dirname(os.path.abspath(__file__))
        top_padding = 530

        self.preview_image = tk.Label(self, text='PREVIEW', font=("TkDefaultFont", 80), fg='white', background="black")
        self.preview_image.place(x=140, y=20, height=360, width=640)

        self.label_select_styl = tk.Label(self, text='Select style: ', font=("TkDefaultFont", 16))
        self.label_select_styl.place(x=44, y=390, height=30, width=120)
        self.style_slider = tk.Label(self, font=("TkDefaultFont", 40), fg='white', background="grey")
        self.style_slider.place(x=42, y=420, height=115, width=835)

        self.label_cont_img = tk.Label(self, text='', font=("TkDefaultFont", 8), background="lightgrey")
        self.label_cont_img.place(x=255, y=top_padding + 20, height=40, width=200)
        self.button_cont_img = tk.Button(self, text='Browse content image', font=("TkDefaultFont", 12),
                                         command=self.browse_image)
        self.button_cont_img.place(x=55, y=top_padding + 20, height=40, width=200)

        self.label_style_img = tk.Label(self, text='', font=("TkDefaultFont", 8), background="lightgrey")
        self.label_style_img.place(x=255, y=top_padding + 62, height=40, width=200)
        self.button_style_img = tk.Button(self, text='Browse style image', font=("TkDefaultFont", 12),
                                          command=self.browse_style)
        self.button_style_img.place(x=55, y=top_padding + 62, height=40, width=200)

        self.choices = [256, 512, 1024, 2048, 4096]
        self.max_dim = tk.IntVar(self)
        self.max_dim.set(self.choices[0])
        self.label_param = tk.Label(self, text='Select sampling size:', font=("TkDefaultFont", 12))
        self.label_param.place(x=55, y=top_padding + 104, height=40, width=200)
        self.choose_box_param = tk.OptionMenu(self, self.max_dim, *self.choices)
        self.choose_box_param.config(font=("TkDefaultFont", 12))
        self.nametowidget(self.choose_box_param.menuname).config(font=("TkDefaultFont", 12))
        self.choose_box_param.place(x=255, y=top_padding + 104, height=40, width=200)

        self.button_transform = tk.Button(self, text='Transfer image', font=44, command=self.transform)
        self.button_transform.place(x=465, y=top_padding + 20, height=60, width=400)

        self.button_save = tk.Button(self, text='Save result', font=44, bg='green', command=self.save_image)
        self.button_save.place(x=465, y=top_padding + 80, height=60, width=400)
        start = 33
        #self.style_img_1 = itk.PhotoImage(file="images/slider/min_the_shipwreck_of_the_minotaur.jpg")
        self.style_img_1 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_the_shipwreck_of_the_minotaur.jpg"))

        self.style_img_1b = tk.Button(self, text="test", image=self.style_img_1,
                                      command=lambda img='images/slider/the_shipwreck_of_the_minotaur.jpg':
                                      self.select_style(img, "The Shipwreck Of The Minotaur"))
        self.style_img_1b.place(x=start+14, y=425)

        self.style_img_2 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_starry_night.jpg"))
        self.style_img_2b = tk.Button(self, text="test", image=self.style_img_2,
                                      command=lambda img='images/slider/starry_night.jpg':
                                      self.select_style(img, "Starry Night"))
        self.style_img_2b.place(x=start+161, y=425)

        self.style_img_3 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_der_schrei.jpg"))
        self.style_img_3b = tk.Button(self, text="test", image=self.style_img_3,
                                      command=lambda img='images/slider/der_schrei.jpg':
                                      self.select_style(img, "Der Schrei"))
        self.style_img_3b.place(x=start+292, y=425)

        self.style_img_4 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_femme_nue_assise.jpg"))
        self.style_img_4b = tk.Button(self, text="test", image=self.style_img_4,
                                      command=lambda img='images/slider/femme_nue_assise.jpg':
                                      self.select_style(img, "Femme Nue Assise"))
        self.style_img_4b.place(x=start+372, y=425)

        self.style_img_5 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_composition.jpg"))
        self.style_img_5b = tk.Button(self, text="test", image=self.style_img_5,
                                      command=lambda img='images/slider/composition.jpg':
                                      self.select_style(img, "Composition"))
        self.style_img_5b.place(x=start+453, y=425)

        self.style_img_6 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_persistence_of_memory.jpg"))
        self.style_img_6b = tk.Button(self, text="test", image=self.style_img_6,
                                      command=lambda img='images/slider/persistence_of_memory.jpg':
                                      self.select_style(img, "Persistence Of Memory"))
        self.style_img_6b.place(x=start+605, y=425)

        self.style_img_7 = itk.PhotoImage(image=PIL.Image.open("images/slider/min_autoportret.jpg"))
        self.style_img_7b = tk.Button(self, text="test", image=self.style_img_7,
                                      command=lambda img='images/slider/autoportret.jpg':
                                      self.select_style(img, "Autoportret"))
        self.style_img_7b.place(x=start+753, y=425)

        self.select_style("")
        # Load the model
        tf.compat.v1.enable_eager_execution()
        self.load_model_h = self.loadModel()

    # Browse image to transform
    def browse_image(self):
        selected_content = filedialog.askopenfilename(initialdir=self.open_file_path,
                                                      title="Select a File",
                                                      filetypes=(("jpeg files", "*.jpg"),
                                                                 ("gif files", "*.gif*"),
                                                                 ("png files", "*.png"),
                                                                 ("all files", "*.*")))

        if selected_content:
            self.open_file_path = os.path.dirname(selected_content)
            self.image_file = selected_content
            self.label_cont_img.config(text=os.path.basename(self.image_file))

    # Browse image to get style from
    def browse_style(self):
        selected_style = filedialog.askopenfilename(initialdir=self.open_style_path,
                                                    title="Select a File",
                                                    filetypes=(("jpeg files", "*.jpg"),
                                                               ("gif files", "*.gif*"),
                                                               ("png files", "*.png"),
                                                               ("all files", "*.*")))

        if selected_style:
            self.open_style_path = os.path.dirname(selected_style)
            self.style_file = selected_style
            self.label_style_img.config(text=os.path.basename(self.style_file))

    # Set chosen style image
    def select_style(self, selected_style, name=""):
        self.style_file = selected_style
        self.label_style_img.config(text=os.path.basename(name))

    # Transform image
    def transform(self):
        if self.image_file == '':
            tk.messagebox.showerror(title="Error", message="Select content image first.")
            return
        elif self.style_file == '':
            tk.messagebox.showerror(title="Error", message="Select style image first.")
            return

        tf.compat.v1.enable_eager_execution()
        # Check if model is loaded
        self.load_model_h.result()

        # Load images
        content_image = self.load_img(self.image_file)
        style_image = self.load_img(self.style_file, self.max_dim.get())
        # Transform image
        stylized_image = self.hub_model(tf.constant(content_image), tf.constant(style_image))[0]
        output_img = self.tensor_to_image(stylized_image)
        self.result = output_img

        # Show transformed image
        output_img = self.resizeImg(output_img)
        output_img = itk.PhotoImage(output_img)
        self.preview_image.config(image=output_img)
        self.preview_image.image = output_img
        self.preview_image.place(x=(920 - output_img.width()) / 2, y=20, height=output_img.height(),
                                 width=output_img.width())

    def save_image(self):
        if self.result is None:
            tk.messagebox.showerror(title="Error", message="There is nothing to save. Transfer an image first.")
            return

        filename = filedialog.asksaveasfile(initialdir="results", mode='wb', defaultextension=".jpg",
                                            filetypes=(("JPEG", "*.jpg"), ("PNG", "*.png"), ("all files", "*.*")))

        if not filename:
            return
        self.result.save(filename)

    @threaded
    @tf.function
    def loadModel(self):
        # Download the model
        model_path = os.path.join("algorithms", "models", "ATS")
        model_file = os.path.join("algorithms", "models", "ATS", "magenta_arbitrary-image-stylization-v1-256_2.tar.gz")
        if not os.path.exists(model_path) or len(os.listdir(model_path)) == 0:
            print("Downloading ATS module")
            if not os.path.exists(model_path):
                os.mkdir(model_path)
            url = 'https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2?tf-hub-format=compressed'
            r = requests.get(url, allow_redirects=True)
            print("ATS downloaded")
            open(model_file, 'wb').write(r.content)
            file = tarfile.open(model_file)
            print("Extracting ATS module")
            file.extractall(model_path)
            file.close()
            os.remove(model_file)

        # Load the model
        print("Loading ATS")
        self.hub_model = hub.load('algorithms/models/ATS')
        print("ATS loaded")

    @staticmethod
    def load_img(path_to_img, max_dim=0):
        img = tf.io.read_file(path_to_img)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.convert_image_dtype(img, tf.float32)

        shape = tf.cast(tf.shape(img)[:-1], tf.float32)
        if max_dim != 0:
            long_dim = max(shape)
            scale = max_dim / long_dim
        else:
            scale = 1

        new_shape = tf.cast(shape * scale, tf.int32)

        img = tf.image.resize(img, new_shape)
        img = img[tf.newaxis, :]
        return img

    @staticmethod
    def tensor_to_image(tensor):
        tensor = tensor * 255
        tensor = np.array(tensor, dtype=np.uint8)
        if np.ndim(tensor) > 3:
            assert tensor.shape[0] == 1
            tensor = tensor[0]
        return Image.fromarray(tensor)

    @staticmethod
    def resizeImg(img):
        width, height = img.size
        scale_h = height / 360
        scale_w = width / 640

        if scale_w <= 1.0 and scale_h <= 1.0:
            return img

        if scale_h > scale_w:
            height = int(height / scale_h)
            width = int(width / scale_h)
        else:
            height = int(height / scale_w)
            width = int(width / scale_w)

        return img.resize((width, height), Image.ANTIALIAS)
