"""
Modern Professional Stylesheet for EcoWipe - Antigravity Theme
"""

MODERN_COLORS = {
    # Primary flat darks
    "primary_start": "#121212",      # Deep dark
    "primary_end": "#121212",        # Flat background
    
    # Secondary colors
    "accent_primary": "#8AB4F8",     # Google Blue
    "accent_secondary": "#A8C7FA",   # Lighter Google Blue
    "accent_tertiary": "#8AB4F8",    # Accent
    
    # Status colors
    "success": "#81C995",            # Soft green
    "warning": "#FDE293",            # Soft amber/yellow
    "danger": "#F28B82",             # Soft red
    "critical": "#E25822",           # Critical red
    
    # UI colors
    "background": "#1E1E1E",         # Surface color
    "surface": "#2D2D2D",            # Lighter surface
    "surface_light": "#383838",      # Even lighter
    "border": "#444444",
    "border_light": "#555555",
    
    # Text colors
    "text_primary": "#E8EAED",
    "text_secondary": "#BCC0C4",
    "text_muted": "#9AA0A6",
    "text_dim": "#80868B"
}

# Modern button styles
MODERN_BUTTON_STYLE = """
    QPushButton {{
        background-color: {color_start};
        color: #121212;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.3px;
    }}
    QPushButton:hover {{
        background-color: {color_start_hover};
    }}
    QPushButton:pressed {{
        background-color: {color_start_press};
    }}
    QPushButton:disabled {{
        background-color: #2D2D2D;
        color: #555555;
    }}
"""

# Modern panel style
MODERN_PANEL_STYLE = """
    QFrame {{
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-radius: 8px;
    }}
"""

# Modern list widget style
MODERN_LIST_STYLE = """
    QListWidget {{
        background-color: #121212;
        color: #E8EAED;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 2px;
        background-color: transparent;
    }}
    QListWidget::item:hover {{
        background-color: #2D2D2D;
    }}
    QListWidget::item:selected {{
        background-color: #383838;
        color: #8AB4F8;
    }}
"""

# Modern combo box style
MODERN_COMBO_STYLE = """
    QComboBox {{
        background-color: #121212;
        color: #E8EAED;
        padding: 8px 12px;
        border: 1px solid #444444;
        border-radius: 6px;
        font-size: 13px;
    }}
    QComboBox:hover {{
        border: 1px solid #8AB4F8;
    }}
    QComboBox:focus {{
        border: 1px solid #8AB4F8;
    }}
    QComboBox::drop-down {{
        border: none;
        background-color: transparent;
    }}
    QComboBox::down-arrow {{
        image: none;
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #1E1E1E;
        color: #E8EAED;
        selection-background-color: #383838;
        selection-color: #8AB4F8;
        border: 1px solid #444444;
        border-radius: 6px;
        outline: none;
    }}
"""

# Modern input style
MODERN_INPUT_STYLE = """
    QLineEdit {{
        background-color: #121212;
        color: #E8EAED;
        padding: 8px 12px;
        border: 1px solid #444444;
        border-radius: 6px;
        font-size: 13px;
        selection-background-color: #383838;
    }}
    QLineEdit:focus {{
        border: 1px solid #8AB4F8;
    }}
    QLineEdit:hover {{
        border: 1px solid #555555;
    }}
"""

# Modern progress bar style
MODERN_PROGRESS_STYLE = """
    QProgressBar {{
        border: none;
        background-color: #2D2D2D;
        border-radius: 4px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: #8AB4F8;
        border-radius: 4px;
    }}
"""

# Modern text edit style
MODERN_TEXTEDIT_STYLE = """
    QTextEdit {{
        background-color: #121212;
        color: #BCC0C4;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 10px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 11px;
        selection-background-color: #383838;
    }}
    QTextEdit:focus {{
        border: 1px solid #555555;
    }}
"""

# Accent text style
ACCENT_TEXT_STYLE = """color: #8AB4F8; font-weight: 500;"""

# Muted text style
MUTED_TEXT_STYLE = """color: #9AA0A6; font-size: 12px;"""

# Primary text style
PRIMARY_TEXT_STYLE = """color: #E8EAED; font-weight: 500;"""
