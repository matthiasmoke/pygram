from src.pygram import Pygram
from src.log import setup_logger

if __name__ == '__main__':
    setup_logger("main")
    pygram: Pygram = Pygram()
    pygram.start()