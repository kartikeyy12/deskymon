import tkinter as tk
from PIL import Image, ImageTk
import os

root = tk.Tk()
root.title("deskymon test")
root.geometry("200x200+500+300")  # fixed position, center-ish
root.configure(bg="yellow")       # bright yellow so we can't miss it

# load psyduck if it exists
sprite_path = os.path.expanduser("~/deskymon/sprites/psyduck.png")
if os.path.exists(sprite_path):
    img = Image.open(sprite_path).convert("RGBA")
    img = img.resize((img.width*4, img.height*4), Image.NEAREST)
    photo = ImageTk.PhotoImage(img)
    tk.Label(root, image=photo, bg="yellow").pack(pady=20)
    tk.Label(root, text="Psyduck!", bg="yellow", font=("Helvetica",14)).pack()
else:
    tk.Label(root, text="No sprite yet", bg="yellow", font=("Helvetica",14)).pack(pady=60)

root.mainloop()
