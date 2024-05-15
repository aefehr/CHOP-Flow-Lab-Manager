from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QLineEdit, QHBoxLayout, QWidget, QPushButton, QSpacerItem, QFrame, QSizePolicy
import sys
import time
from PySide6.QtCore import Qt

'''
This module is for independent functions.
To consider: move all independent functions to this module.
'''

def set_labels_properties(label_1, label_2):
    ''' 1) Set the width of two QLabels equal to the width of the widest QLabel.
        2) Right-align the text.
    '''
    largest_label_width = 0
    # get the widths
    for label in [label_1, label_2]:
        largest_label_width = max(largest_label_width, label.sizeHint().width())
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    # set the width of the labels equal to the max. width
    for label in [label_1, label_2]:
        label.setFixedWidth(largest_label_width)



def test_set_labels_properties():
    '''This function is for testing set_labels_properties()'''
    app = QApplication()
    widget = QWidget()
    label_1 = QLabel("Label 1")
    label_2 = QLabel("Label_2 longer text")   
    layout=QVBoxLayout()
    widget.setLayout(layout)         
    for _ in [label_1, label_2]: 
        layout.addWidget(_)
        _.setStyleSheet("background-color: pink;")

    set_labels_properties(label_1, label_2)
    
    widget.show()  
    sys.exit(app.exec())




def get_screen_geometry():
    ''' Get the geometries of all available screens.'''
    screens = QApplication.screens()
    # Start with the first screen's geometry
    screen_0_geometry = screens[0].geometry()
    combined_geometry = screen_0_geometry

    # Combine the geometries of all screens
    for screen in screens[1:]:
        combined_geometry = combined_geometry.united(screen.geometry())
        screen_height = max(screen_0_geometry.height(), combined_geometry.height()) - 50
    return combined_geometry, screen_0_geometry




def make_js_code_for_get_property_with_xpath(xpath_string, html_property):
        """this function generates the js code for getting the HTML property of the element @XPATH"""
        # property can be 'textContent', 'innerHTML', 'id', 'parentElement', ,'className', 'value', 'checked', 'selected'
        # 'attributes', 'clientHeight', 'clientWidth', 'href', 'src', style
        if xpath_string:
            js_code = f"""
            var element = document.evaluate("{xpath_string}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            element ? element.{html_property} : '';
            """
        else:
            None
        return js_code



def make_js_code_to_set_value(xpath_string, html_property):
    # "//input[@id='login']"  "//input[@id='password_input']"   html_property is typically 'textContent'
    js_code =   """
                var xpath = "{xpath}";
                var element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {{
                    element.value = "{elem_value}";
                }} else {{
                    console.warn('Element with XPath ' + xpath + ' not found.');
                }}
                """.format(xpath=xpath_string, elem_value=html_property)
    return js_code



def make_js_code_for_action(xpath_string):       #, html_action = 'click()'):       # ("//button[@id='login_btn']", "click()"
    js_code = """
                var xpath = "{xpath}";
                var element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {{
                    element.click();
                }} else {{
                    console.warn('Element with xpath ' + xpath + ' not found.');
                }}
                """.format(xpath=xpath_string)
    return js_code



if __name__ == "__main__":

    string_made = make_js_code_for_get_property_with_xpath("//input[@id='login']", 'textContent')
    print(string_made)    
    
    string_made = make_js_code_to_set_value("//input[@id='login']", 'textContent')
    print(string_made)  

    string_made = make_js_code_for_action("//button[@id='login_btn']")
    print(string_made)  
    
    test_set_labels_properties()