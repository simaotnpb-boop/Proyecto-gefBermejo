#!/usr/bin/env python3
"""
Punto de entrada principal para el Generador Pro de Códigos QR Personalizados.
"""

import sys
from gui import QRGeneratorApp


def main():
    try:
        app = QRGeneratorApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

