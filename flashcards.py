import tkinter as tk
from tkinter import messagebox
import csv
import os
import random

VOCAB_FILE = "vocab.csv"

DEFAULT_CARDS = [
    ("ephemeral", "Lasting for a very short time."),
    ("loquacious", "Tending to talk a great deal; talkative."),
    ("succinct", "Briefly and clearly expressed."),
    ("ubiquitous", "Present, appearing, or found everywhere."),
]

THEME = {
    "bg": "#070814",        # deep space
    "card": "#0E1030",      # dark purple
    "card2": "#101846",     # slightly brighter
    "text": "#E8E9FF",
    "muted": "#A8ACD6",
    "outline": "#23265A",
    "btn_bg": "#1B1F55",
    "btn_hover": "#262B6A",
    "btn_disabled": "#141738",
    "accent_purple": "#7C3AED",
    "accent_blue": "#2563EB",
    "accent_red": "#EF4444",
    "good": "#22C55E",
    "bad": "#EF4444",
}

def center_window(root: tk.Tk, w: int, h: int) -> None:
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

class GalaxyFlashcards:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Galaxy Vocab Flashcards")
        self.root.configure(bg=THEME["bg"])
        self.root.resizable(False, False)

        # state
        self.cards: list[tuple[str, str]] = []
        self.index = -1
        self.showing_definition = False
        self.correct = 0
        self.completed = 0  # increments when you go to next card

        # background canvas
        self.canvas = tk.Canvas(self.root, bg=THEME["bg"], highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_background()

        # main container
        self.container = tk.Frame(self.root, bg=THEME["bg"])
        self.container.place(relx=0.5, rely=0.5, anchor="center")

        # header
        self.header = tk.Label(
            self.container,
            text="🌌 Galaxy Flashcards",
            font=("Segoe UI", 18, "bold"),
            fg=THEME["text"],
            bg=THEME["bg"]
        )
        self.header.pack(pady=(0, 12))

        # card frame
        self.card = tk.Frame(
            self.container,
            bg=THEME["card"],
            highlightthickness=1,
            highlightbackground=THEME["outline"]
        )
        self.card.pack(padx=18, pady=6)

        self.term_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 26, "bold"),
            fg=THEME["text"],
            bg=THEME["card"],
            wraplength=680,
            justify="center",
            padx=20,
            pady=18,
        )
        self.term_label.pack()

        self.def_label = tk.Label(
            self.card,
            text="",
            font=("Segoe UI", 13),
            fg=THEME["muted"],
            bg=THEME["card"],
            wraplength=680,
            justify="center",
            padx=20,
            pady=12,
        )
        self.def_label.pack()

        # buttons row
        self.buttons = tk.Frame(self.container, bg=THEME["bg"])
        self.buttons.pack(pady=14)

        self.show_btn_wrap, self.show_btn = self._accent_button(
            self.buttons, "Show Definition", self.toggle_definition, THEME["accent_blue"]
        )
        self.show_btn_wrap.grid(row=0, column=0, padx=8)

        self.good_btn_wrap, self.good_btn = self._accent_button(
            self.buttons, "I Got It", lambda: self.mark(True), THEME["good"]
        )
        self.good_btn_wrap.grid(row=0, column=1, padx=8)

        self.bad_btn_wrap, self.bad_btn = self._accent_button(
            self.buttons, "I Missed It", lambda: self.mark(False), THEME["bad"]
        )
        self.bad_btn_wrap.grid(row=0, column=2, padx=8)

        # status
        self.status = tk.Label(
            self.container,
            text="",
            font=("Segoe UI", 10),
            fg=THEME["muted"],
            bg=THEME["bg"]
        )
        self.status.pack(pady=(2, 0))

        # load + start
        self._set_answer_buttons(False)
        self.load_cards()

        if self.cards:
            self.next_card()
        else:
            self.term_label.config(text="No cards loaded")
            self.def_label.config(text=f"Place {VOCAB_FILE} beside this app.\nFormat: term,definition")
            self.show_btn.config(state=tk.DISABLED)

        self._update_status()

    # ---------- UI helpers ----------
    def _accent_button(self, parent, text, command, accent_color):
        wrapper = tk.Frame(parent, bg=accent_color, padx=2, pady=2)

        btn = tk.Button(
            wrapper,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold"),
            fg=THEME["text"],
            bg=THEME["btn_bg"],
            activeforeground=THEME["text"],
            activebackground=THEME["btn_hover"],
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            cursor="hand2"
        )
        btn.pack(fill="both", expand=True)

        def on_enter(_=None):
            if btn["state"] != tk.DISABLED:
                btn.config(bg=THEME["btn_hover"])

        def on_leave(_=None):
            if btn["state"] != tk.DISABLED:
                btn.config(bg=THEME["btn_bg"])

        wrapper.bind("<Enter>", on_enter)
        wrapper.bind("<Leave>", on_leave)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return wrapper, btn

    def _set_button_state(self, btn: tk.Button, state: str):
        btn.config(state=state)
        if state == tk.DISABLED:
            btn.config(bg=THEME["btn_disabled"], cursor="")
        else:
            btn.config(bg=THEME["btn_bg"], cursor="hand2")

    def _set_answer_buttons(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self._set_button_state(self.good_btn, state)
        self._set_button_state(self.bad_btn, state)

    def _draw_background(self):
        self.canvas.delete("all")
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w < 10 or h < 10:
            w, h = 760, 520

        # “nebula” blobs
        for _ in range(10):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(80, 180)
            color = random.choice(["#0D1133", "#0B1238", "#130A2E", "#120A25"])
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="")

        # stars
        for _ in range(240):
            x = random.randint(0, w)
            y = random.randint(0, h)
            size = random.choice([1, 1, 1, 2, 2, 3])
            color = random.choice(["#FFFFFF", "#DDE3FF", "#C7D2FE", "#FDE68A"])
            self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")

        # streak accents
        for _ in range(10):
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            x2 = x1 + random.randint(40, 140)
            y2 = y1 + random.randint(-12, 12)
            color = random.choice([THEME["accent_purple"], THEME["accent_blue"], THEME["accent_red"]])
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

    # ---------- CSV loading (correct try/except pattern) ----------
    def load_cards(self):
        try:
            self.cards = self._load_cards_from_csv(VOCAB_FILE)
            if not self.cards:
                raise ValueError("No valid term/definition rows found.")
            random.shuffle(self.cards)

        except FileNotFoundError:
            self.cards = DEFAULT_CARDS.copy()
            random.shuffle(self.cards)

        except PermissionError:
            self.cards = DEFAULT_CARDS.copy()
            random.shuffle(self.cards)
            messagebox.showwarning(
                "Vocab file not readable",
                f"Couldn't read {VOCAB_FILE} (permission issue).\nUsing default cards."
            )

        except Exception as e:
            self.cards = DEFAULT_CARDS.copy()
            random.shuffle(self.cards)
            messagebox.showerror(
                "Error loading vocab",
                f"Couldn't load {VOCAB_FILE}.\n\nReason: {e}\n\nUsing default cards."
            )

    def _load_cards_from_csv(self, path: str) -> list[tuple[str, str]]:
        cards: list[tuple[str, str]] = []
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if not row or len(row) < 2:
                    continue
                term = (row[0] or "").strip()
                definition = (row[1] or "").strip()

                # skip header if present
                if i == 0 and term.lower() in {"term", "word"} and definition.lower() in {"definition", "meaning"}:
                    continue

                if term and definition:
                    cards.append((term, definition))
        return cards

    # ---------- Flashcard flow ----------
    def next_card(self):
        if not self.cards:
            self.term_label.config(text="No cards available")
            self.def_label.config(text="")
            self.show_btn.config(state=tk.DISABLED)
            self._set_answer_buttons(False)
            self._update_status()
            return

        self.index = (self.index + 1) % len(self.cards)
        term, _ = self.cards[self.index]

        self.term_label.config(text=term)
        self.def_label.config(text="")
        self.showing_definition = False

        self.show_btn.config(text="Show Definition", state=tk.NORMAL)
        self._set_answer_buttons(False)
        self._update_status()

    def toggle_definition(self):
        if self.index < 0 or not self.cards:
            return

        term, definition = self.cards[self.index]

        if not self.showing_definition:
            self.def_label.config(text=definition)
            self.showing_definition = True
            self.show_btn.config(text="Next Card")
            self._set_answer_buttons(True)
        else:
            self.completed += 1
            self.next_card()

    def mark(self, got_it: bool):
        if got_it:
            self.correct += 1
        self._set_answer_buttons(False)
        self._update_status()

    def _update_status(self):
        accuracy = (self.correct / self.completed * 100.0) if self.completed else 0.0
        self.status.config(
            text=f"Completed: {self.completed}   •   Correct: {self.correct}   •   Accuracy: {accuracy:.1f}%"
        )

if __name__ == "__main__":
    root = tk.Tk()
    center_window(root, 760, 520)
    app = GalaxyFlashcards(root)
    root.mainloop()
