import customtkinter as ctk

from models import TournamentModel
from bracket_canvas import TournamentBracketCanvas
from control_window import ControlWindow


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")

    root = ctk.CTk()
    root.title("Turneringsbrakett - Hovedvindu")

    tournament_model = TournamentModel()
    bracket_canvas = TournamentBracketCanvas(root, tournament_model)
    control_window = ControlWindow(root, tournament_model, bracket_canvas)

    root.mainloop()