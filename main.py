from src.Pygram import Pygram
from src.log import setup_logger

if __name__ == '__main__':
    setup_logger("main")
    pygram = Pygram()
    pygram.start()