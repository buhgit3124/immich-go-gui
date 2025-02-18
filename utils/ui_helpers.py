# immich_go_gui/utils/ui_helpers.py

from PySide6.QtWidgets import QLabel

def create_info_icon(tooltip):
    """Creates a QLabel with an (i) icon and a tooltip."""
    label = QLabel("(i)")
    label.setToolTip(tooltip)
    label.setStyleSheet("color: #666; font-style: italic;")
    return label