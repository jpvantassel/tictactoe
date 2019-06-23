import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
from checkwin import checkwin
from decideplay import decideplay
from evalboard import evalboard, set_diffuse, nd3_to_tuple
from transform import board_transform
from inversetransform import board_itransform
from updateboard import updateboard
from plotforhuman import determinecell, updateplot, plotstate, plotforhuman
from updateutility import update_utility, flip_player


# Decide on current player
ask_for_input = True
while ask_for_input:
    human_player = int(input("Please enter player number 1 or 2: "))
    if human_player in (1, 2):
        ask_for_input = False
    else:
        print("Player {} not recognized, enter 1 or 2".format(human_player))

# Enter game difficulty
ask_for_input = True
while ask_for_input:
    difficulty = input("Please enter game difficulty E, M, or H: ")
    if difficulty in ("E", "M", "H", "T"):
        ask_for_input = False
    else:
        print("Diffculty setting {} not recognized, enter E, M, or H".format(difficulty))

# Decide on difficulty
if difficulty in ("E",):
    number_simulation = 1000
elif difficulty in ("M",):
    number_simulation = 100000
elif difficulty in ("H",):
    number_simulation = 100000000
elif difficulty in ("T",):
    number_simulation = 1

# Decide on which file to load
if human_player == 1:
    file_name_p2 = "training_p2_"+str(number_simulation)
    machine_player = 2
    fnames = {machine_player: file_name_p2}
    players = (human_player, machine_player)
    p1 = human_player
    p2 = machine_player
else:
    file_name_p1 = "training_p1_"+str(number_simulation)
    machine_player = 1
    fnames = {machine_player: file_name_p1}
    players = (machine_player, human_player)
    p1 = machine_player
    p2 = human_player

# Default settings
reward_win = 1
punish_loss = -1

# Load previous training sets for computer
boards_played = {}
if os.path.isfile(fnames[machine_player]):
    with open(fnames[machine_player], "rb") as f:
        boards_played[machine_player] = pickle.load(f)
else:
    boards_played[machine_player] = {}

# Setup a loop for mutliple games, back to back
continue_playing = True
while continue_playing:

    # Initialize new game
    state = np.zeros((3, 3))
    win = False
    draw = False
    current_game_boards = {human_player: [], machine_player: []}
    current_game_move = {human_player: [], machine_player: []}

    # Loop through a single game, at most 5 moves for a single player
    for game_move in range(5):
        # Switch between players
        for current_player in players:
            if current_player == human_player:
                move = plotforhuman(state, current_player)
            else:
                board_state = evalboard(state,
                                        boards_played[current_player],
                                        p1=p1,
                                        p2=p2,
                                        )
                current_game_boards[current_player] += [board_state[1]]

                # Add entry to the boards_played
                if len(board_state) > 3:
                    boards_played[current_player].update(
                        {board_state[1]: board_state[0]})
                # Decide the move
                move, tran_move = decideplay(board_state[0],
                                             board_state[2])

                current_game_move[current_player] += [tran_move]

            # Make the move, and update state
            state = updateboard(state, move, current_player)

            # Check if there is a winner, after three moves, as none before.
            if game_move >= 2:
                win = checkwin(state, p1=p1, p2=p2)
                if win:
                    winning_player = current_player
                    losing_player = p1 if current_player == p2 else p2
                elif ((game_move == 4) & (current_player == p1)):
                    draw = True
                    fig, ax = plotstate(state)
                    plt.title("It's a Tie!")
                    fig.show()
            if win | draw:
                break
        if win | draw:
            break

    # Update utility
    if win:
        fig, ax = plotstate(state)
        txt="You Win!" if winning_player is human_player else "Computer Wins!"
        plt.title(txt)    
        fig.show()

        boards_played = update_utility(boards_played,
                                        current_game_boards,
                                        current_game_move,
                                        machine_player,
                                        winning_player,
                                        losing_player,
                                        reward_win,
                                        punish_loss,
                                        flag_indirect=False,
                                        )

    # Decide if you want to continue
    ask_for_input = True
    while ask_for_input:
        continue_text = input("Would you like to play again (Y/N)? ")
        if continue_text == "N":
            ask_for_input = False
            continue_playing = False
        elif continue_text == "Y":
            plt.close('all')
            ask_for_input = False
        else:
            print("Response {} not recognized, use Y or N".format(continue_text))

# Save out training
with open(fnames[machine_player], "wb") as f:
    pickle.dump((boards_played[machine_player]), f)
