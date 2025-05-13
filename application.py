import streamlit as st
import plotly
from manager import RevenueManager

st.set_page_config(page_title="Rev-Data", layout='wide')
st.title("Welcome to Rev-Data!")

manager = RevenueManager()

####-----Side Bar Navigation -----###

st.sidebar.header("Navigation")

page = st.sidebar.radio("Go to", ["Login", "Create a Book", "Add Rooms", "Add Fares", "Add Nights",
                                  "Add Roomnights","Business on the Books","Forecast", "Rates and Hurdle Rates", "LogOut"])

st.sidebar.markdown("---")

st.sidebar.write("Current book")

book_num = st.session_state.get("book_num")

if book_num is not None:
    st.sidebar.success(f"Book {book_num}")

else:
    st.sidebar.info("No book selected")


### Page logic ###

if page == "Login":
    st.subheader("Login to your book")
    login_book = st.text_input("Enter your book number")
    login_password = st.text_input("Enter your password", type="password")

    if st.button("Log In"):
        try:
            login_book_int = int(login_book)
            book = manager.booksdict.get(login_book_int)

            if not book:
                st.error("Book not found")
            elif book.password != login_password:
                st.error("Wrong Password")
            else:
                st.session_state['book_num'] = login_book_int
                st.session_state['password'] = login_password
                st.success(f"Welcome back {book.name}!")
        except:
            st.error("Plese wait for the support")
    
    st.divider()
    st.subheader("Rev-Data News and Updates")

    books = len(manager.booksdict.keys())
    st.subheader(f"Did you know that Rev-Data counts with {books} total clients!")
   



if page == "Create a Book":
    manager.open_book()

elif page == "Add Rooms":
    if "book_num" in st.session_state:
        manager.create_rooms()
        manager.show_rooms()
    else:
        st.warning("Please create or log into a book first.")

elif page == "Add Fares":
    if "book_num" in st.session_state:
        manager.create_rates()
        manager.show_rates()
    else:
        st.warning("Please create or log into a book first.")

elif page == "Add Nights":
    if "book_num" in st.session_state:
        manager.create_nights()
    else:
        st.warning("Please create or log into a book first.")

elif page == "Add Roomnights":
    if "book_num" in st.session_state:
        manager.create_roomnights()
        manager.show_roomnights()
    else:
        st.warning("Please create or log into a book first.")

elif page == "Business on the Books":
    if "book_num" in st.session_state:
        manager.show_bob()
    else:
        st.warning('Please create or log into a book first.')

elif page == "Forecast":
    st.subheader("Forecasting")
    manager.show_forecast()

elif page == "Rates and Hurdle Rates":
    st.subheader("Rates")
    manager.show_rate_optimization()



elif page == "LogOut":
    st.subheader("🚪 Log Out")
    if st.button("Do you wish to log out?"):
    
        if "book_num" in st.session_state:
            st.success(f"Successfully logged out of Book #{st.session_state['book_num']}")
            del st.session_state["book_num"]
        else:
            st.info("You are not logged into any book.")
