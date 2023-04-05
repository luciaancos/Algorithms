from game import MillGame, GameMode
from mill_game_exceptions import MillGameException


def delete_chip(game: MillGame):
    print("\nCONGRATULATIONS! you have made a mill")
    print(game.board)
    ring = int(
        input(
            "Introduce the ring of the chip you want to remove, choose between 0-2:\n> "
        )
    )
    cell = int(
        input(
            "Introduce the cell of the chip you want to remove, choose between 0-7:\n> "
        )
    )
    try:
        game.remove(ring, cell)
    except MillGameException as error:
        print("\nERROR:", error)


def main():
    game = MillGame()

    while game.mode != GameMode.FINISHED:
        match game.mode:
            case GameMode.PLACE:
                print("\nIt is", game.turn.name, " player turn")
                print(game.board, "\n")
                ring = int(
                    input(
                        "Introduce the ring where you want to place your chip, "
                        "choose between 0-2:\n> "
                    )
                )
                cell = int(
                    input(
                        "Introduce the cell where you want to place your chip, "
                        "choose between 0-7:\n> "
                    )
                )
                try:
                    game.place(ring, cell)
                except MillGameException as error:
                    print("\nERROR:", error)

                while game.has_to_delete:
                    delete_chip(game)

            case GameMode.MOVE:
                print("\nIt is", game.turn.name, " player turn")
                print(game.board, "\n")
                ring1 = int(
                    input(
                        "Select the ring of the chip ypu want to move, choose between 0-2:\n> "
                    )
                )
                cell1 = int(
                    input(
                        "Select the cell of the chip you want to move, choose between 0-7:\n> "
                    )
                )
                ring2 = int(
                    input(
                        "Select the ring where you want to move the chip, choose between 0-2:\n> "
                    )
                )
                cell2 = int(
                    input(
                        "Select the cell where you want to move the chip, choose between 0-7::\n> "
                    )
                )
                try:
                    game.move(ring1, cell1, ring2, cell2)
                except MillGameException as error:
                    print("\nERROR:", error)

                while game.has_to_delete:
                    delete_chip(game)

    if game.winner is None:
        print(
            f"{game.max_movements} movements have been made so the game is considered a tie"
        )
    else:
        print(f"CONGRATULATIONS {game.winner.name} PLAYER, YOU HAVE WON")
    print("End of the game...")


if __name__ == "__main__":
    main()
