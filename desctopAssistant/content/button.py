import customtkinter as ctk

class AppButton(ctk.CTkButton):
    def __init__(self, master, text, height, width, action_func, x, y, font_size=14):
        super().__init__(master, width=width, height=height, text=text, command=action_func,font=("Arial", font_size))
        self.place(x=x, y=y)
