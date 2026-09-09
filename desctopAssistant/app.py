import customtkinter as ctk

from content.button import AppButton

class AssisnantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Desktop Assitant")
        self.geometry("400x300")
        self.configure(bg="white")

        # self.label = ctk.CTkLabel(self, text="Welcome to the Desktop Assistant", font=("Arial", 16))
        # self.label.pack(pady=20)

        self.messages_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="white"
        )
        
        self.messages_frame.pack(side="left", padx=20)
    
        
        self.btn_start = AppButton(master=self, action_func=self.on_click_start, height=150, width=150, x=500, y=400, text="Start")
        self.btn_start.pack(side="right", padx=20)

    def on_click_start(self):
        print("START")


def start():
    # python manage.py run_assistant
    pass