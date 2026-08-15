"""
main.py
Point d'entrée de Badringo for English.
"""

from database.db import init_db
from gui.app import lancer_application


def main():
    init_db()
    lancer_application()


if __name__ == "__main__":
    main()
