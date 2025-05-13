import streamlit as st
import pandas as pd 
from book import Book
import pandas as pd
import os
import pickle
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

class RevenueManager():
    def __init__(self):
        self.booksdict = {}
        self.next_book_number = 0
        self.data_dir = 'books_data'
        os.makedirs(self.data_dir, exist_ok=True)
        self.load_all_books() #Load the existing books in the memory
        self.forecast_horizon = 60

###----- METHODS TO STORE AND WRITE TO DATABASE OR FILE----###


    def save_book(self, book_num):
        #save book to disk
        book = self.booksdict[book_num]
        with open(f"{self.data_dir}/book_{book_num}.pkl", "wb") as f:
            pickle.dump(book, f)
    
    def load_all_books(self):
        #Load all books saved in disk when app starts
        for file in os.listdir(self.data_dir):
            if file.startswith("book_") and file.endswith(".pkl"):
                book_number = int(file.split("_")[1].split(".")[0])
                with open(f"{self.data_dir}/{file}", "rb") as f:
                    book = pickle.load(f)
                    self.booksdict[book_number] = book
                    self.next_book_number = max(self.next_book_number, book_number + 1)

    def create_book(self, name, password):
        #Create a book
        book = Book(name, password)
        new_book_number = self.next_book_number         
        self.booksdict[new_book_number] = book
        self.save_book(new_book_number) #save after creation
        self.next_book_number += 1
        return new_book_number
    

###------ STREAMLIT UI METHODS FOR BETTER INTERFACE-----#####

    def open_book(self):
        st.write("📘Welcome to Rev-Data! Let's Create your Book!")
        name = st.text_input("🏨Enter your hotel name")
        password = st.text_input("🔐Create a password", type='password')

        if st.button("🚀Create Book"):
            book_number = self.create_book(name, password)
            st.session_state["book_num"] = book_number
            st.session_state['password'] = password
            st.success(f"Book Created!🎉, your book number is **{book_number}**")


    def create_rooms(self):
        st.write("🛏️ Upload Rooms")
        file = st.file_uploader("📄 Upload your hotel rooms CSV", type='csv')
        if st.button("Create Rooms"):
            if not file:
                st.error("Upload a CSV first.")
                return
            df = pd.read_csv(file)
            self.create_rooms_from_session(df)
    
    def create_rates(self):
        st.write("💲 Upload Rates for your hotel")
        file = st.file_uploader("📄 Upload your pricing CSV", type='csv')
        if st.button("Create Fare Classes"):
            if not file:
                st.error("Upload a CSV first.")
                return
            df = pd.read_csv(file)
            self.create_rates_from_session(df)

    def create_nights(self):
        st.write("📆 Upload Night Structure")
        file = st.file_uploader("📄 Upload night structure CSV", type='csv')
        if st.button("Create Nights"):
            if not file:
                st.error("Upload a CSV first.")
                return
            df = pd.read_csv(file)
            self.create_nights_from_session(df)

    def create_roomnights(self):
        st.write("📈 Upload Historical RoomNights")
        file = st.file_uploader("📄 Upload historical data CSV", type='csv')
        if st.button("Create RoomNights"):
            if not file:
                st.error("Upload a CSV first.")
                return
            df = pd.read_csv(file)
            self.create_roomnights_from_session(df)

    def show_rooms(self):
       st.write("Hotel's Rooms and Room Types")
       self.show_rooms_from_session()

    def show_rates(self):
        st.write("Hotels Rates")
        self.show_rates_from_session()

    def show_roomnights(self):
        book = self.get_logged_in_book()
        if book:
            for night in book.nights.values():
                st.write(f"For date {night.date} with {len(night.roomnights)}")
    
        else:
            st.wirte("What")



#####------- METHODS FOR LOGIC (NO USER INTERFACE)-----####
    def create_rooms_from_session(self, df):
        book = self.get_logged_in_book()
        if book:
            book.create_room(df, st.session_state['password'])
            self.save_book(st.session_state["book_num"])
            st.success("Rooms created Succesfully")

    def create_rates_from_session(self,df):
        book = self.get_logged_in_book()
        if book:
            book.create_fareclass(df, st.session_state['password'])
            self.save_book(st.session_state["book_num"])
            st.success("Fare Classes created Succesfully")
    
    def create_nights_from_session(self, df):
        book = self.get_logged_in_book()
        if book:
            book.create_nights(df, st.session_state['password'])
            self.save_book(st.session_state["book_num"])
            st.success("Nights created Succesfully")

    def create_roomnights_from_session(self, df):
        book = self.get_logged_in_book()
        if book:
            book.create_roomnight(df, st.session_state["password"])
            self.save_book(st.session_state["book_num"])
            st.success("Our Revenue Manager knows all about your hotel now!")

    def get_logged_in_book(self):
        book_num = st.session_state.get("book_num")
        password = st.session_state.get("password")

        if book_num is None or password is None:
            st.error("You must create or log in into a book first")
            return None
        book = self.booksdict.get(book_num)        
        return book
    
    def show_rooms_from_session(self):
        book = self.get_logged_in_book()
        if book:
            book.show_rooms()

    def show_rates_from_session(self):
        book = self.get_logged_in_book()
        if book:
            book.show_rates()
    def show_room_nights(self):
        book = self.get_logged_in_book()
        if book:
            book.show_roomnight()

    def show_bob(self):
        if "book_num" in st.session_state:
            st.title(f"Business on the Books (Next {self.forecast_horizon} Days)")
            book = self.get_logged_in_book()

            if book:
                if st.button("Generate Future Data"):
                    with st.spinner("Generating Future Data..."):
                        today = datetime.now().date()
                        book.create_future_nights(today, self.forecast_horizon)
                        book.generate_and_create_future_roomnights(self.forecast_horizon)
                        self.save_book(st.session_state['book_num'])
                        st.success(f"Future data generated and saved for {book.name}!")

                # Load the book AFTER potential generation
                book = self.get_logged_in_book()
                if book:
                    df_bob = book.bob(st.session_state['password'], forecasting_days=self.forecast_horizon)
                    self.save_book(st.session_state['book_num'])
                    if df_bob is not None:
                        st.dataframe(df_bob[['Date', 'DOW', 'Available Rooms', 'Total Occupied', 
                                             'Occupancy', 'Revenue', 'ADR', 'RevPar']], hide_index=True)
                        st.divider()
                        st.subheader("Dashboard")
                        selected_date = st.date_input("Select a Date for Dashboard")
                        

                        if selected_date:
                            night = book.nights.get(selected_date)
                            st.write(f"{night.date}")
                            available_rooms = night.available_rooms
                            total_occupied = night.occupied
                            occupancy = night.occupancy
                            capacity = night.capacity
                            adr = night.adr
                            revenue = night.revenue
                            revpar = night.revpar
                            last_year_date = selected_date - timedelta(days=(365))
                            lynight = book.nights.get(last_year_date)
                            lyadr = lynight.calculate_adr()
                            lyrevpar = lynight.calculate_revpar()
                            lyrevenue = lynight.total_revenue()
                            

                            labels = ['Occupied', 'Available']
                            values = [total_occupied, available_rooms]
                            fig_occupancy_pie = go.Figure(data=[go.Pie(labels=labels, values=values)])
                            fig_occupancy_pie.update_layout(title='Occupancy Pie Chart')
                            st.plotly_chart(fig_occupancy_pie)
                            

                            fag_comparison = go.Figure()
                            fag_comparison.add_trace(go.Bar(x=['ADR', 'Last Years ADR'], y=[adr,lyadr], name='ADR'))
                            fag_comparison.add_trace(go.Bar(x = ['Revpar', 'Last Year RevPar'], y = [revpar, lyrevpar], name='RevPar', marker_color=['rgb(136,204,238)', 'rgb(102,197,204)']))
                            fag_comparison.update_layout(title=f"Comparison with {last_year_date}")
                            st.plotly_chart(fag_comparison)

                    else:
                        st.info("No booking data available.")
                else:
                    st.info("No book loaded.")
            else:
                st.warning('Please create or log into a book first.')
    
    def show_forecast(self):
        if "book_num" in st.session_state:
            st.title("Occupancy Forecast")
            book = self.get_logged_in_book()

            if book:
                # Get the BOB data directly from the Book object
                bob_df = book.bob(st.session_state['password'], forecasting_days=self.forecast_horizon)
                st.subheader(f"Forecast for {book.name}")

                if bob_df is not None:
                    fig = px.bar(bob_df,
                                 x='Date',
                                 y=['Group', 'Transient'],
                                 title='Forecast and Supply',
                                 color_discrete_map={
                                     'Transient': 'rgb(179,205,227)',
                                     'Group': 'rgb(204,235,197)'
                    })
                    fig.add_trace(go.Scatter(
                        x = bob_df['Date'],
                        y = bob_df['Total Rooms'],
                        mode='lines',
                        name='Capacity',
                        line=dict(color='rgb(255,242,174)')
                    ))
                    fig.add_trace(go.Scatter(
                        x = bob_df['Date'],
                        y = bob_df['Unconstrained Demand'],
                        mode = 'lines+markers',
                        name= "Unconstrained Demand",
                        line=dict(color='rgb(251,180,174)')
                    ))
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Rooms',
                        legend_title='Fields'
                    )
                st.plotly_chart(fig)
                st.divider()
                st.dataframe(bob_df[['Date', 'DOW', 'Remaining Demand', 'Unconstrained Demand', 'Forecast Occupancy']])


            else:
                st.info("No booking data available to display forecast.")

    def show_rate_optimization(self):
        if "book_num" in st.session_state:
            st.title("Rate Optimization")
            book = self.get_logged_in_book()

            if book:
                df_bob = book.bob(st.session_state['password'], self.forecast_horizon) # Get bob_df
                st.subheader(f"Rates and Hurdle for {book.name}")

                if df_bob is not None:
                    

                    with st.spinner("Calculating Optimized Rates..."):
                        book.rates(st.session_state['password'], self.forecast_horizon, df_bob) 
                        self.save_book(st.session_state['book_num'])
                        st.success(f"Rates Calculated for hotel {book.name}")

                    st.subheader(f"Optimized 'Retail' Rate per Night (Next {self.forecast_horizon} Days)")
                    optimized_rates_data = []
                    today = datetime.now().date()
                    for i in range(self.forecast_horizon):
                        current_date = today + timedelta(days=i)
                        if current_date in book.nights:
                            night = book.nights[current_date]
                            optimized_rates_data.append({"Date": current_date, "Optimized Rate": night.optimized_rate, "Bid Prices": night.bidprice})

                    if optimized_rates_data:
                        df_optimized_rates = pd.DataFrame(optimized_rates_data)
                        
                        st.dataframe(df_optimized_rates, hide_index=True)
                        st.divider()
                        st.subheader("Optimized Rates")
                        fig = px.line(
                            df_optimized_rates,
                            x='Date',
                            y= "Optimized Rate",
                            markers=True,
                        )
                        st.plotly_chart(fig)

                        fag = px.scatter(
                            df_optimized_rates,
                            x='Date',
                            y='Bid Prices',
                            color='Bid Prices',
                            color_continuous_scale='Viridis',
                            text='Bid Prices',
                            size_max=30
                        )
                        fag.update_layout(
                            title='Hurlde Point for the next days'
                        )
                        st.divider()
                        st.plotly_chart(fag)

                    else:
                        st.info("No rate data available.")
    

