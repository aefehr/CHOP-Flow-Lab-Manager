from PySide6.QtGui import QFont, QGuiApplication, QPalette, QColor
from PySide6.QtCore import Qt

# Styling is not used consistently throughout the app
#TODO consider using qss for styling

# ===========================================================================
class Colors():
    blue_0 = QColor(0,85,135)      # exact, darkest CHOP blue
    blue_1 = QColor(65,182,230)    # exact,    
    blue_2 = QColor(99,195,234)    # approx.
    blue_3 = QColor(138,210,240)   # approx.
    blue_4 = QColor(177,225,245)   # approx.
    blue_5 = QColor(216,240,250)   # approx., lightest CHOP blue


def get_chop_palette(app=None):
    chop_palette = app.palette()
    chop_palette.setColor( QPalette.Window, Colors.blue_3) 
    chop_palette.setColor( QPalette.WindowText, Colors.blue_0)
    chop_palette.setColor( QPalette.Disabled, QPalette.WindowText, QColor( 127, 127, 127 ) )
    chop_palette.setColor( QPalette.Base, Qt.white )
    chop_palette.setColor( QPalette.AlternateBase, Qt.red)  ### ???
    chop_palette.setColor( QPalette.ToolTipBase, Qt.white )
    chop_palette.setColor( QPalette.ToolTipText, Qt.white )
    chop_palette.setColor( QPalette.Text, Colors.blue_0)                      
    chop_palette.setColor( QPalette.Disabled, QPalette.Text, QColor( 127, 127, 127 ) )
    chop_palette.setColor( QPalette.Dark, QColor( 35, 35, 35 ) )
    chop_palette.setColor( QPalette.Shadow, QColor( 20, 20, 20 ) )
    chop_palette.setColor( QPalette.Button, Colors.blue_5 )
    chop_palette.setColor( QPalette.ButtonText, Colors.blue_0)
    chop_palette.setColor( QPalette.Disabled, QPalette.ButtonText, QColor( 127, 127, 127 ) )
    chop_palette.setColor( QPalette.BrightText, Qt.red )
    chop_palette.setColor( QPalette.Link, QColor( 42, 130, 218 ) )
    chop_palette.setColor( QPalette.Highlight, QColor( 42, 130, 218 ) )
    chop_palette.setColor( QPalette.Disabled, QPalette.Highlight, QColor( 80, 80, 80 ) )
    chop_palette.setColor( QPalette.HighlightedText, Qt.white )
    chop_palette.setColor( QPalette.Disabled, QPalette.HighlightedText, QColor( 127, 127, 127 ), )
    
    return chop_palette


# Probably there is a better way to set the font size (?!?)
def regular_font():
    regular_font = QFont()
    return regular_font

def bold_font():
    bold_font = QFont()
    bold_font.setBold(True)
    return bold_font

def title_font():
    title_font = QFont("Arial Rounded MT Bold", 40)
    # title_font.setBold(True)
    return title_font

def subtitle_font():
    subtitle_font = QFont("Arial Rounded MT Bold", 20)
    return subtitle_font
