# tw_stock_system/main.py
from interface.menu import CLI

if __name__ == "__main__":
    app = CLI()
    try:
        app.main_loop()
    except KeyboardInterrupt:
        print("\nForce Quit.")