#!/usr/bin/env python3
"""
Tic-Tac-Toe Console Game
Features:
- Single Player (AI Easy/Normal/Hard) & Multiplayer
- Persistent Scoreboard & Save/Load functionality (JSON)
- Minimax AI with depth scoring (plays optimally)
- 3x3 Grid with color support
"""

import json
import os
import random
import sys
import time
from typing import Dict, List, Optional, Tuple, Union

SAVE_FILE = "tictactoe_save.json"

# --------------------------
# 1. Colors & Graphics
# --------------------------
USE_COLOR = True

# Check for color support
try:
    import colorama
    colorama.init()
except ImportError:
    pass

def supports_color() -> bool:
    # Check if stdout is a terminal and NO_COLOR is not set
    return os.getenv("NO_COLOR") is None and sys.stdout.isatty()

USE_COLOR = USE_COLOR and supports_color()

def colored(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

def color_x(s: str) -> str: return colored(s, "1;31")   # Red
def color_o(s: str) -> str: return colored(s, "1;36")   # Cyan
def color_title(s: str) -> str: return colored(s, "1;35") # Magenta
def color_ok(s: str) -> str: return colored(s, "1;32")    # Green
def color_warn(s: str) -> str: return colored(s, "1;33")  # Yellow
def color_err(s: str) -> str: return colored(s, "1;31")   # Red

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# --------------------------
# 2. Board Logic
# --------------------------
WIN_LINES = [
    (0,1,2),(3,4,5),(6,7,8), # Rows
    (0,3,6),(1,4,7),(2,5,8), # Cols
    (0,4,8),(2,4,6)          # Diagonals
]

def empty_board() -> List[str]:
    return [" "] * 9

def board_display(board: List[str]) -> str:
    """Returns the board string with colors and grid lines."""
    cells = []
    for i, v in enumerate(board, 1):
        if v == "X":
            cells.append(color_x(" X "))
        elif v == "O":
            cells.append(color_o(" O "))
        else:
            # Show number 1-9 faintly if supported, else plain
            cells.append(colored(f" {i} ", "90")) # Dark gray for numbers

    return (
        f"\n"
        f" {cells[0]}|{cells[1]}|{cells[2]}\n"
        f" ---+---+---\n"
        f" {cells[3]}|{cells[4]}|{cells[5]}\n"
        f" ---+---+---\n"
        f" {cells[6]}|{cells[7]}|{cells[8]}\n"
    )

def check_winner(board: List[str]) -> Optional[str]:
    """Returns 'X', 'O', 'Draw', or None (if game continues)."""
    for a, b, c in WIN_LINES:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "Draw"
    return None

def available_moves(board: List[str]) -> List[int]:
    return [i for i, v in enumerate(board) if v == " "]

# --------------------------
# 3. AI Implementations
# --------------------------
def ai_easy(board: List[str], symbol: str) -> int:
    """Random valid move."""
    return random.choice(available_moves(board))

def ai_normal(board: List[str], symbol: str) -> int:
    """Heuristic: Win -> Block -> Center -> Corner -> Random."""
    opponent = "O" if symbol == "X" else "X"
    moves = available_moves(board)

    # 1. Take winning move
    for m in moves:
        b = board.copy()
        b[m] = symbol
        if check_winner(b) == symbol:
            return m

    # 2. Block opponent winning move
    for m in moves:
        b = board.copy()
        b[m] = opponent
        if check_winner(b) == opponent:
            return m

    # 3. Prefer Center
    if 4 in moves:
        return 4

    # 4. Prefer Corners
    corners = [c for c in [0, 2, 6, 8] if c in moves]
    if corners:
        return random.choice(corners)

    # 5. Any
    return random.choice(moves)

def minimax(board: List[str], depth: int, is_maximizing: bool, ai_symbol: str, opp_symbol: str) -> int:
    """
    Minimax recursive algorithm with depth scoring.
    Returns score: +10 for AI win, -10 for Opponent win, 0 for Draw.
    Adjusted by depth to prefer faster wins / slower losses.
    """
    winner = check_winner(board)
    if winner == ai_symbol:
        return 10 - depth
    if winner == opp_symbol:
        return depth - 10
    if winner == "Draw":
        return 0

    if is_maximizing:
        best_score = -1000
        for m in available_moves(board):
            board[m] = ai_symbol
            score = minimax(board, depth + 1, False, ai_symbol, opp_symbol)
            board[m] = " "
            best_score = max(score, best_score)
        return best_score
    else:
        best_score = 1000
        for m in available_moves(board):
            board[m] = opp_symbol
            score = minimax(board, depth + 1, True, ai_symbol, opp_symbol)
            board[m] = " "
            best_score = min(score, best_score)
        return best_score

def ai_hard(board: List[str], symbol: str) -> int:
    """Optimal play using Minimax."""
    opponent = "O" if symbol == "X" else "X"
    best_score = -1000
    best_move = None
    
    # If it's the very first move of the game, take center to save computation
    if len(available_moves(board)) == 9:
        return 4

    for m in available_moves(board):
        board[m] = symbol
        score = minimax(board, 0, False, symbol, opponent)
        board[m] = " "
        
        if score > best_score:
            best_score = score
            best_move = m
            
    return best_move if best_move is not None else random.choice(available_moves(board))

AI_ENGINES = {
    "easy": ai_easy,
    "normal": ai_normal,
    "hard": ai_hard
}

# --------------------------
# 4. Save/Load & Scoreboard
# --------------------------
def default_stats() -> Dict[str, int]:
    return {"games": 0, "wins": 0, "losses": 0, "draws": 0}

def get_stats(scoreboard: Dict, name: str) -> Dict[str, int]:
    if name not in scoreboard:
        scoreboard[name] = default_stats()
    return scoreboard[name]

def update_scoreboard(scoreboard: Dict, p1_name: str, p2_name: str, result: str, p1_sym: str):
    """Update stats after game end."""
    s1 = get_stats(scoreboard, p1_name)
    s2 = get_stats(scoreboard, p2_name)

    s1["games"] += 1
    s2["games"] += 1

    if result == "Draw":
        s1["draws"] += 1
        s2["draws"] += 1
    else:
        # result is "X" or "O"
        if p1_sym == result:
            s1["wins"] += 1
            s2["losses"] += 1
        else:
            s1["losses"] += 1
            s2["wins"] += 1

def load_data() -> Dict:
    if not os.path.exists(SAVE_FILE):
        return {"saved_game": None, "scoreboard": {}}
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"saved_game": None, "scoreboard": {}}

def save_data(saved_game: Optional[Dict], scoreboard: Dict):
    data = {"saved_game": saved_game, "scoreboard": scoreboard}
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except IOError:
        print(color_err("Warning: Could not save file."))

def print_scoreboard(scoreboard: Dict):
    clear_screen()
    print(color_title("=== HALL OF FAME ==="))
    if not scoreboard:
        print("No stats recorded yet.")
        input("\nPress Enter to return...")
        return

    # Sort option
    print("Sort by: (1) Win Rate  (2) Total Wins")
    choice = input("Choice [1]: ").strip()
    
    items = list(scoreboard.items())
    
    def get_wr(stats):
        return (stats["wins"] / stats["games"]) if stats["games"] > 0 else 0

    if choice == "2":
        items.sort(key=lambda x: x[1]["wins"], reverse=True)
    else:
        items.sort(key=lambda x: (get_wr(x[1]), x[1]["wins"]), reverse=True)

    print(f"\n{'PLAYER':<15} {'G':<4} {'W':<4} {'L':<4} {'D':<4} {'WIN %':<6}")
    print("-" * 45)
    for name, s in items:
        wr = get_wr(s) * 100
        print(f"{name:<15} {s['games']:<4} {s['wins']:<4} {s['losses']:<4} {s['draws']:<4} {wr:<5.1f}")
    
    input("\nPress Enter to return...")

# --------------------------
# 5. Game Loop & Logic
# --------------------------
def parse_input(raw: str) -> Tuple[str, Optional[int]]:
    """Parses move (1-9 or r,c) or command (save, quit)."""
    raw = raw.strip().lower()
    if raw in ["save", "s"]: return "save", None
    if raw in ["quit", "q", "exit"]: return "quit", None
    
    # Coordinates r,c
    if "," in raw:
        try:
            parts = raw.split(",")
            r, c = int(parts[0]), int(parts[1])
            if 1 <= r <= 3 and 1 <= c <= 3:
                return "move", (r-1)*3 + (c-1)
        except ValueError:
            pass
            
    # Number 1-9
    if raw.isdigit():
        val = int(raw)
        if 1 <= val <= 9:
            return "move", val - 1
            
    return "invalid", None

def play_game(state: Dict, scoreboard: Dict) -> str:
    """
    Main game loop.
    Returns: 'menu', 'replay', or 'exit'
    """
    board = state["board"]
    p1 = state["p1"] # Dict with name, symbol, is_ai
    p2 = state["p2"]

    # Ensure history exists
    state["history"] = state.get("history", [])
    
    while True:
        clear_screen()
        # Header
        mode_str = f"Single Player ({state.get('difficulty','Normal')})" if state["mode"] == "single" else "Multiplayer"
        print(color_title(f"=== TIC TAC TOE: {mode_str} ==="))
        print(f"{p1['name']} ({color_x(p1['symbol'])})  vs  {p2['name']} ({color_o(p2['symbol'])})")
        print(board_display(board))
        print(color_warn("Commands: 'save', 'quit'"))

        # Check Win/Draw
        winner = check_winner(board)
        if winner:
            update_scoreboard(scoreboard, p1["name"], p2["name"], winner, p1["symbol"])
            # Clear save file on game over
            save_data(None, scoreboard) 
            
            print("\n" + "-"*30)
            if winner == "Draw":
                print(color_warn(" GAME OVER: It's a Draw!"))
            else:
                w_name = p1["name"] if p1["symbol"] == winner else p2["name"]
                color_func = color_x if winner == "X" else color_o
                print(color_func(f" GAME OVER: {w_name} ({winner}) Wins!"))
            
            # Show updated mini-stats
            print("-" * 30)
            for p in [p1, p2]:
                s = get_stats(scoreboard, p["name"])
                print(f"{p['name']}: {s['wins']}W - {s['losses']}L - {s['draws']}D")
            
            # Post-game menu
            while True:
                c = input("\n(r) Replay | (m) Menu | (e) Exit: ").strip().lower()
                if c == 'r': return 'replay'
                if c == 'm': return 'menu'
                if c == 'e': return 'exit'

        # Determine Turn
        current_player = p1 if state["turn"] == p1["symbol"] else p2
        symbol = current_player["symbol"]
        
        # AI Move
        if current_player["is_ai"]:
            print(f"\n{current_player['name']} is thinking...")
            time.sleep(0.6) # Small delay for UX
            move = AI_ENGINES[state["difficulty"]](board, symbol)
            board[move] = symbol
            state["history"].append({"player": current_player["name"], "symbol": symbol, "move": move})
            state["turn"] = "O" if symbol == "X" else "X"
            continue

        # Human Move
        raw = input(f"\n{current_player['name']} ({symbol}), enter move (1-9 or row,col): ")
        action, val = parse_input(raw)

        if action == "save":
            save_data(state, scoreboard)
            print(color_ok("Game Saved! Returning to main menu..."))
            time.sleep(1)
            return "menu"
        
        if action == "quit":
            print("Returning to menu (unsaved progress lost unless saved).")
            time.sleep(1)
            return "menu"
        
        if action == "move" and val is not None:
            if board[val] == " ":
                board[val] = symbol
                state["history"].append({"player": current_player["name"], "symbol": symbol, "move": val})
                state["turn"] = "O" if symbol == "X" else "X"
            else:
                print(color_err("Cell occupied!"))
                time.sleep(1)
        else:
            print(color_err("Invalid input! Use 1-9 or row,col."))
            time.sleep(1)

# --------------------------
# 6. Menus & Setup
# --------------------------
def setup_new_game() -> Dict:
    clear_screen()
    print(color_title("--- NEW GAME SETUP ---"))
    
    print("Select Mode:")
    print("1. Single Player (vs Computer)")
    print("2. Multiplayer (Human vs Human)")
    mode_in = input("Choice [1]: ").strip()
    is_multi = (mode_in == "2")
    
    p1_name = input("\nEnter Player 1 Name [Player1]: ").strip() or "Player1"
    
    if is_multi:
        p2_name = input("Enter Player 2 Name [Player2]: ").strip() or "Player2"
        # Explicitly ask who plays X
        print(f"\nWho plays as {color_x('X')} (goes first)?")
        print(f"1. {p1_name}")
        print(f"2. {p2_name}")
        who_x = input("Choice [1]: ").strip()
        
        if who_x == "2":
            # P2 is X
            p1_data = {"name": p2_name, "symbol": "X", "is_ai": False}
            p2_data = {"name": p1_name, "symbol": "O", "is_ai": False}
        else:
            # P1 is X
            p1_data = {"name": p1_name, "symbol": "X", "is_ai": False}
            p2_data = {"name": p2_name, "symbol": "O", "is_ai": False}
            
        difficulty = None
        mode = "multi"
    else:
        # Single Player
        print("\nChoose Difficulty:")
        print("1. Easy (Random)")
        print("2. Normal (Balanced)")
        print("3. Hard (Unbeatable)")
        diff_map = {"1":"easy", "2":"normal", "3":"hard"}
        diff_in = input("Choice [2]: ").strip()
        difficulty = diff_map.get(diff_in, "normal")
        
        # Symbol choice
        sym = input("\nPlay as X (first) or O (second)? [X]: ").strip().upper()
        if sym != "O": sym = "X"
        
        human_sym = sym
        ai_sym = "O" if sym == "X" else "X"
        
        human = {"name": p1_name, "symbol": human_sym, "is_ai": False}
        comp = {"name": "Computer", "symbol": ai_sym, "is_ai": True}
        
        # P1 is always X in our state logic (turn holder), but we map names to symbols
        if human_sym == "X":
            p1_data, p2_data = human, comp
        else:
            p1_data, p2_data = comp, human
            
        mode = "single"

    return {
        "board": empty_board(),
        "turn": "X", # X always starts
        "mode": mode,
        "difficulty": difficulty,
        "p1": p1_data,
        "p2": p2_data,
        "history": []
    }

def main_menu():
    while True:
        data = load_data()
        scoreboard = data.get("scoreboard", {})
        saved_game = data.get("saved_game")
        
        clear_screen()
        print(color_title("======================="))
        print(color_title("   TIC TAC TOE PRO     "))
        print(color_title("======================="))
        print(f"1. New Game")
        msg = "Continue Game"
        if saved_game:
            print(f"2. {colored(msg, '1;32')} (Turn: {saved_game['turn']})")
        else:
            print(f"2. {colored(msg, '90')} (No save)")
        print(f"3. Scoreboard")
        print(f"4. Exit")
        
        choice = input("\nSelect: ").strip()
        
        if choice == "1":
            state = setup_new_game()
            while True:
                res = play_game(state, scoreboard)
                if res == "menu": break
                if res == "exit": sys.exit()
                if res == "replay":
                    # Keep same settings, reset board
                    state["board"] = empty_board()
                    state["turn"] = "X"
                    state["history"] = []
                    
        elif choice == "2":
            if not saved_game:
                print(color_err("\nNo saved game found!"))
                time.sleep(1)
                continue
            state = saved_game
            while True:
                res = play_game(state, scoreboard)
                if res == "menu": break
                if res == "exit": sys.exit()
                if res == "replay":
                    # If they replay from a loaded game, we usually keep the old settings
                    # but we must reset the board.
                    state["board"] = empty_board()
                    state["turn"] = "X"
                    state["history"] = []

        elif choice == "3":
            print_scoreboard(scoreboard)
            
        elif choice == "4":
            print(color_ok("\nThanks for playing!"))
            sys.exit()

if __name__ == "__main__":
    main_menu()