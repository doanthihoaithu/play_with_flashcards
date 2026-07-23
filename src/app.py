import streamlit as st

from config import load_config


def main() -> None:
    config = load_config()
    app_title = config.get("app_title", "English Flashcards")
    st.set_page_config(page_title=app_title, page_icon="\U0001F5C2️", layout="centered")

    pages = st.navigation(
        [
            st.Page("pages/introduction.py", title="Introduction", icon="👋", default=True),
            st.Page("pages/flashcards.py", title="Flashcards", icon="\U0001F5C2️"),
            st.Page("pages/shadowing.py", title="Shadowing", icon="🎧"),
        ]
    )
    pages.run()


if __name__ == "__main__":
    main()