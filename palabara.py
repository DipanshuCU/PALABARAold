from tkinter import ttk
from pathlib import Path

import tkinter as tk
import random
import string
import sys


WORD_LEN = 5
MAX_TRIES = 6
COLOR_BORDER_HIGHLIGHT = "#565758"
COLOR_BLANK = "#121213"
COLOR_INCORRECT = "#3a3a3c"
COLOR_HALF_CORRECT = "#b59f3b"
COLOR_CORRECT = "#538d4e"
BOX_SIZE = 55
PADDING = 3

try:
    BASE_PATH = Path(sys._MEIPASS)
except AttributeError:
    BASE_PATH = Path(".")

VALID_WORDS_WORDLIST = BASE_PATH / "wordlists/wordle-allowed-guesses.txt"
ANSWERS_WORDLIST = BASE_PATH / "wordlists/wordle-answers.txt"
APP_ICON = BASE_PATH / "assets/wordle_logo_32x32.png"
BACKSPACE_ICON = BASE_PATH / "assets/backspace.png"
HELP_ICON = BASE_PATH / "assets/help.png"
SETTINGS_ICON = BASE_PATH / "assets/settings.png"
MANUAL_IMAGE = BASE_PATH / "assets/manual_image2.png"

ANSWERS = set(word.upper() for word in open(ANSWERS_WORDLIST).read().splitlines())
ALL_WORDS = (
    set(word.upper() for word in open(VALID_WORDS_WORDLIST).read().splitlines())
    | ANSWERS
)


class MainScreen(tk.Frame):
    def __init__(self, master, controller, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.controller = controller

        self.bind("<Return>", self.check_word)
        self.bind("<BackSpace>", self.remove_letter)
        self.bind("<Key>", self.enter_letter)

        self.init_ui()

    def init_ui(self):
        self.icons = {
            "settings": tk.PhotoImage(file=SETTINGS_ICON),
            "help": tk.PhotoImage(file=HELP_ICON),
            "backspace": tk.PhotoImage(file=BACKSPACE_ICON),
        }

        
        # ==> main game grid ==>
        # if there is extra space then give it to main game grid
        self.rowconfigure(3, weight=1)

        container = tk.Frame(self, bg=COLOR_BLANK)
        container.grid()

        self.labels = []
        for i in range(MAX_TRIES):
            row = []
            for j in range(WORD_LEN):
                cell = tk.Frame(
                    container,
                    width=BOX_SIZE,
                    height=BOX_SIZE,
                    highlightthickness=1,
                    highlightbackground=COLOR_INCORRECT,
                )
                cell.grid_propagate(0)
                cell.grid_rowconfigure(0, weight=1)
                cell.grid_columnconfigure(0, weight=1)
                cell.grid(row=i, column=j, padx=PADDING, pady=PADDING)
                t = tk.Label(
                    cell,
                    text="",
                    justify="center",
                    font=("Helvetica Neue", 24, "bold"),
                    bg=COLOR_BLANK,
                    fg="#d7dadc",
                    highlightthickness=1,
                    highlightbackground=COLOR_BLANK,
                )
                t.grid(sticky="nswe")
                row.append(t)
            self.labels.append(row)
        # <== main game grid <==

        # bottom empty separator
        tk.Frame(self, bg=COLOR_BLANK, height=45).grid()

        # ==> virtual keyboard ==>
        container = tk.Frame(self, bg=COLOR_BLANK)
        container.grid()

        # add all the alphabets
        self.keyboard_buttons = {}
        for i, keys in enumerate(["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]):
            row = tk.Frame(container, bg=COLOR_BLANK)
            row.grid(row=i, column=0)

            for j, c in enumerate(keys):
                if i == 2:  # leave one column for the ENTER button in the last row
                    j += 1

                cell = tk.Frame(
                    row,
                    width=40,
                    height=55,
                    highlightthickness=1,
                    highlightbackground=COLOR_INCORRECT,
                )
                cell.grid_propagate(0)
                cell.grid_rowconfigure(0, weight=1)
                cell.grid_columnconfigure(0, weight=1)
                cell.grid(row=0, column=j, padx=PADDING, pady=PADDING)
                btn = tk.Button(
                    cell,
                    text=c,
                    justify="center",
                    font=("Helvetica Neue", 13),
                    bg=COLOR_BLANK,
                    fg="#d7dadc",
                    cursor="hand2",
                    border=0,
                    command=lambda c=c: self.enter_letter(key=c),
                )
                btn.grid(sticky="nswe")
                self.keyboard_buttons[c] = btn

        for col in (0, 8):
            text = "ENTER" if col == 0 else ""
            func = self.check_word if col == 0 else self.remove_letter
            cell = tk.Frame(
                row,
                width=75,
                height=55,
                highlightthickness=1,
                highlightbackground=COLOR_INCORRECT,
            )
            cell.grid_propagate(0)
            cell.grid_rowconfigure(0, weight=1)
            cell.grid_columnconfigure(0, weight=1)
            cell.grid(row=0, column=col, padx=PADDING, pady=PADDING)
            btn = tk.Button(
                cell,
                text=text,
                justify="center",
                font=("Helvetica Neue", 13),
                bg=COLOR_BLANK,
                fg="#d7dadc",
                cursor="hand2",
                border=0,
                command=func,
            )
            btn.grid(row=0, column=0, sticky="nswe")

        # set the image for delete button
        btn.configure(image=self.icons["backspace"])
        # <== virtual keyboard <==

    def toast(self, message, duration=2):
        """show a toast message which will disappear after {duration} seconds"""
        t = tk.Label(self.top_separator, text=message, font=("Helvetica Neue", 16))
        t.grid(row=0, column=0, sticky="news", padx=5, pady=5)
        self.master.after(duration * 1000, lambda: t.grid_remove())

    def update_keyboard(self):
        for key, btn in self.keyboard_buttons.items():
            if key in self.correct_letters:
                btn["bg"] = COLOR_CORRECT
            elif key in self.half_correct_letter:
                btn["bg"] = COLOR_HALF_CORRECT
            elif key in self.incorrect_letters:
                btn["bg"] = COLOR_INCORRECT
            else:
                btn["bg"] = COLOR_BLANK

    def update_labels(self, colors=None):
        word = self.words[self.current_word]
        for i, label in enumerate(self.labels[self.current_word]):
            try:
                letter = word[i]
            except IndexError:
                letter = ""

            label["text"] = letter
            if colors:
                label["bg"] = colors[i]
                label["highlightbackground"] = colors[i]
            else:
                label["bg"] = COLOR_BLANK
                label["highlightbackground"] = (
                    COLOR_BORDER_HIGHLIGHT if letter else COLOR_BLANK
                )

    def check_word(self, event=None):
        print("checking word:", self.words[self.current_word])
        word = self.words[self.current_word]
        if len(word) < WORD_LEN:
            # messagebox.showinfo("You're an Idiot.", "Not Enough Letters.")
            self.toast("Not Enough Letters")
            return

        if word not in ALL_WORDS:
            # messagebox.showinfo("You're an Idiot.", "Word is not in wordlist.")
            self.toast("Not in word list")
            return

        colors = []
        freq = {c: self.answer.count(c) for c in self.answer}
        for x, y in zip(word, self.answer):
            if x == y:
                colors.append(COLOR_CORRECT)
                self.correct_letters.add(x)
            elif freq.get(x, 0) > 0:
                colors.append(COLOR_HALF_CORRECT)
                self.half_correct_letter.add(x)
                freq[x] -= 1
            else:
                self.incorrect_letters.add(x)
                colors.append(COLOR_INCORRECT)
        self.update_labels(colors)
        self.update_keyboard()

        self.current_word += 1
        if word == self.answer:
            self.congratulate()
        elif self.current_word >= MAX_TRIES:
            self.humiliate()

    def remove_letter(self, event=None):
        if self.words[self.current_word]:
            print(self.words[self.current_word][-1], "was deleted.")
            self.words[self.current_word] = self.words[self.current_word][:-1]
            self.update_labels()

    def enter_letter(self, event=None, key=None):
        key = key or event.keysym.upper()
        if key in string.ascii_uppercase:
            print(key, "was entered.")
            self.words[self.current_word] += key
            # prevent user from enterering excess letters
            self.words[self.current_word] = self.words[self.current_word][:WORD_LEN]
            self.update_labels()


class WordleApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Wordle - A Word Game")
        self.state("zoomed")
        # self.resizable(False, False)
        self.app_icon = tk.PhotoImage(file=APP_ICON)
        self.iconphoto(False, self.app_icon)

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self, bg=COLOR_BLANK)
        container.grid(sticky="news")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.frames["MainScreen"] = MainScreen(
            master=container, controller=self, bg=COLOR_BLANK
        )

        # put all of the pages in the same location;
        # the one on the top of the stacking order
        # will be the one that is visible.
        self.frames["MainScreen"].grid(row=0, column=0, sticky="ns")

        # show the main screen
        self.show_frame("MainScreen")

        self.fullscreen = False
        self.bind("<F11>", self.fullscreen_toggle)

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        frame = self.frames[page_name]
        # set the frame focus so that we can capture keyboard events inside this frame
        frame.focus_set()
        # raise the frame to the top of the stack so that it is visible
        frame.tkraise()

    def fullscreen_toggle(self, event=None):
        """Toggle fullscreen mode"""
        if self.fullscreen:
            self.wm_attributes("-fullscreen", False)
            self.fullscreen = False
        else:
            self.wm_attributes("-fullscreen", True)
            self.fullscreen = True
    

if __name__ == "__main__":
    WordleApp().mainloop()

"""
sample error message for when you lose:
    "You're a dumbo"
    "Go to Pre-KG and learn English"
    "Wow, you're so bad"
"""
