import sys
from frontend.main_gui import BigGui
from PySide6.QtWidgets import QApplication
import json

def main():
    """
    Entry point for the entire application, initializes the main GUI.
    """
    app = QApplication(sys.argv)
    with open('config.json', 'r') as config_file:
        config_dict = json.load(config_file)
    
    main_window = BigGui(config_dict)
    main_window.show()
    app.setStyle("Fusion")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
