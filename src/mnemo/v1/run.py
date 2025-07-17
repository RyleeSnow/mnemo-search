import os
import sys


def main():
    script = os.path.join(os.path.dirname(__file__), "app.py")
    os.execvp("streamlit", ["streamlit", "run", script] + sys.argv[1:])

if __name__ == "__main__":
    main()