import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None

ROLES = ["User", "Admin"]


def login():
    st.title("Brainsmith Dashboard")
    st.header("Log in")
    role = st.selectbox("Choose your role", ROLES)

    if st.button("Log in"):
        st.session_state.role = role
        st.rerun()


def logout():
    st.session_state.role = None
    st.rerun()


role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("pages/settings.py", title="Settings", icon=":material/settings:")
chatbot_page = st.Page(
    "pages/chatbot.py", 
    title="Chatbot", 
    icon=":material/chat:",
    default=(role == "User"),
)
embedder_page = st.Page(
    "pages/embedder.py", 
    title="Embedder", 
    icon=":material/book:",
    default=(role == "Admin"),
)

account_pages = [logout_page, settings]
user_pages = [chatbot_page]
admin_pages = [embedder_page]

# TODO: Find proper images for the logo
# st.logo("images/horizontal_blue.png", icon_image="images/icon_blue.png")

page_dict = {}
if st.session_state.role in ["User", "Admin"]:
    page_dict["User"] = user_pages
if st.session_state.role == "Admin":
    page_dict["Admin"] = admin_pages

if len(page_dict) > 0:
    pg = st.navigation({"General": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()