import streamlit as st
from app.models.night import Night
from app.models.room import Room
import numpy as np
from app.models.roomnight import RoomNight
import pandas as pd
from app.models.fareclass import FareClass
from datetime import timedelta, datetime
from livereservation import LiveReservaitonGenerator

class Book():
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.capacity = 0
        self.nights = {}
        self.pricing = {}
        self.rooms = {}
        self.live_reservation_generator = None

    def create_room(self, room_df: pd.DataFrame, password):
        if password != self.password:
            return

        if password == self.password:
            for _, row in room_df.iterrows():
                room_id = str(row['Room_id'])  # Convert to string here
                print(f"Room ID type: {type(room_id)}, value: {room_id}")  # Keep this for confirmation
                room = Room(room_id, row['Room Type'])
                self.rooms[room_id] = room
            capacity = len(self.rooms.keys())
            self.capacity = capacity
    
    def create_fareclass(self, df_prices: pd.DataFrame, password):
        if password != self.password:
            return
        
        if password == self.password:
            for _, row in df_prices.iterrows():
                name = row['Name']
                code = row['Code']
                max_rate = row['Max']
                min_rate = row['Min']
                price = FareClass(name, code, max_rate, min_rate)
                self.pricing[row['Name']] = price
            self._initialize_live_reservation()
    
    def _initialize_live_reservation(self):
        if self.pricing and self.rooms:
            market_segments = list(self.pricing.keys())
            num_rooms = len(self.rooms)
            self.live_reservation_generator = LiveReservaitonGenerator(
                self.pricing, market_segments, num_hotels=1, rooms_per_hotel=num_rooms
            )
            

    def create_nights(self, df:pd.DataFrame, password):
        if password != self.password:
            return 
        
        if password == self.password:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            unique_dates = df['Date'].unique()
            for d in unique_dates:
                if d not in self.nights:
                    self.nights[d] = Night(d)
    
    def create_roomnight(self, df: pd.DataFrame, password):
        if password != self.password:
            return
        st.write(f"debug book {self.rooms}")

        for d, n in self.nights.items():
            n.create_roomnight(df, self.rooms)

    def create_future_nights(self, start_date: datetime.date, forecast_days = int):
        for i in range(forecast_days):
            future_date = start_date + timedelta(days=i)
            if future_date not in self.nights:
                self.nights[future_date] = Night(future_date)

    def generate_and_create_future_roomnights(self, forecast_days):
        """Generates live reservations and creates RoomNight objects for the future."""
        if self.live_reservation_generator:
            # Removed the call to _get_existing_future_room_nights
            future_bookings_df = self.live_reservation_generator.generate_next_reservations(
                forecast_days, None  # Pass None as existing_room_nights for now
            )

            if not future_bookings_df.empty:
                self._create_roomnights_from_df(future_bookings_df)
        else:
            print("Live reservation generator not initialized.")

    def _get_existing_future_room_nights(self, forecast_days):
        future_room_nights = []
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=forecast_days)
        for date, night in self.nights.items():
            if start_date <= date < end_date:
                future_room_nights.extend(night.roomnights)
        return future_room_nights
    
    def _create_roomnights_from_df(self, df: pd.DataFrame):
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        grouped_reservations = df.groupby('Date')

        for date_str, reservations_group in grouped_reservations:
            date = pd.to_datetime(date_str).date()
            if date in self.nights:
                night = self.nights[date]
                # Clear existing roomnights for the future date BEFORE adding new ones
                night.roomnights = []
                added_rooms_for_night = set()
                for _, row in reservations_group.iterrows():
                    room_id = row['Room Id']
                    if room_id in self.rooms and room_id not in added_rooms_for_night:
                        room = self.rooms[room_id]
                        is_sold = int(row.get('is_sold', 0))
                        fare_class = row.get('Market Segment', None)
                        rate = float(row.get('Rate', 0.0))
                        los = int(row.get('LOS', 0))
                        
                        booking_date_raw = row.get('Booking Date', None)
                        booking_date = pd.to_datetime(booking_date_raw).date() if pd.notna(booking_date_raw) else None
                        dba = (date - booking_date).days if booking_date else None
                        
                        rn = RoomNight(room, is_sold, fare_class, rate, los, dba)
                        night.roomnights.append(rn)
                        added_rooms_for_night.add(room_id)

    
    def show_rooms(self):
        for room in self.rooms.values():
            room.show()

    def show_rates(self):
        for rate in self.pricing.values():
            rate.show()
    def show_roomnight(self):
        for night in self.nights.values():
            night.show_roomnights()

#### ----- METHODS FOR REVENUE MANAGEMENT ----- ###
    
    def get_night_occupancy(self, night):
        total_rooms = len(self.rooms) # Get total rooms from the Book
        sold_rooms = night.occupied_rooms()
        return (sold_rooms / total_rooms) * 100 if total_rooms > 0 else 0
    
    def forecast_occupancy_for_night(self, forecast_night):
        today = datetime.today().date()
        forecast_dba = (forecast_night.date - today).days
        forecast_day_of_week = forecast_night.date.weekday() #date in numbers
        
        relevant_historical_data = []
        for historical_date, historical_night in self.nights.items():
            if historical_date < today:
                historical_day_of_week = historical_date.weekday()
                if historical_day_of_week == forecast_day_of_week:
                    historical_dba = (historical_date - (today - timedelta(days=forecast_dba))).days
                    if -3 <= historical_dba <= 3:
                        relevant_historical_data.append(self.get_night_occupancy(historical_night))
        if relevant_historical_data:
            return sum(relevant_historical_data) / len(relevant_historical_data)
        else:
            return 0
        

    def get_historical_adr_for_night(self, future_date, dba, fareclass):
        historical_adrs = []
        future_dow = future_date.weekday()
        today = datetime.today().date()
        future_dba = (future_date - today).days
        for hist_date, his_night in self.nights.items():
            if hist_date < today and hist_date.weekday == future_dow:
                hist_dba = (hist_date - (today - timedelta(days=future_dba))).days
                for rn in his_night.roomnights:
                    if rn.fareclass == fareclass and abs(hist_dba) <= 3 and rn.rate > 0:
                        historical_adrs.append(rn.rate)
        return historical_adrs

    def bob(self, password, forecasting_days):
        if password != self.password:
            return
        else:
            bob_data = []
            today_gt = datetime.today().date()
            end_date_future = today_gt + timedelta(days=forecasting_days)
            st.write(f"Today's date in Book.bob: {today_gt}")
            st.write(f"End date future in Book.bob: {end_date_future}")

            for date, night in self.nights.items():
                include_night = False
                if today_gt <= date < end_date_future:
                    include_night = True
                    

                if include_night:
                    
                    if night.roomnights:
                        
                        day_of_week = night.date.strftime('%A')
                        total_rooms = night.total_rooms()
                        available_rooms = night.calculate_available_rooms()
                        group_occupied = night.group_occupied()
                        
                        transient_occupied = night.transient_occupied()
                        
                        occupied = night.occupied_rooms()
                        occupancy_percentage = night.calculate_occupancy()
                        revenue = night.total_revenue()
                        adr = night.calculate_adr()
                        revpar = night.calculate_revpar()


                        forecasted_percentage = 0
                        forecasted_occupied = 0
                        if date > today_gt:
                            forecasted_night = Night(date)
                            if date in self.nights:
                                forecasted_night.roomnights = self.nights[date].roomnights
                            forecasted_percentage = self.forecast_occupancy_for_night(forecasted_night)
                            forecasted_occupied = round(total_rooms * (forecasted_percentage / 100))

                            

                        bob_data.append({
                            "Date": date,
                            "DOW": day_of_week,
                            "Total Rooms": total_rooms,
                            "Group": group_occupied,
                            "Transient": transient_occupied,
                            "Total Occupied": occupied,
                            "Available Rooms": available_rooms,
                            "Occupancy": round(occupancy_percentage * 100,0),
                            "Remaining Demand": forecasted_occupied,
                            "Revenue": revenue,
                            "ADR": adr,
                            "RevPar": revpar
                        })
            

            df = pd.DataFrame(bob_data)

            df['Unconstrained Demand'] = df.loc[:, "Total Occupied"].astype(int) + df.loc[:, 'Remaining Demand'].astype(int)
            df['Forecast Occupancy'] = (df["Total Occupied"] + df['Remaining Demand']) / df["Total Rooms"]
            df["Forecast Occupancy"] = df['Forecast Occupancy'].clip(upper=1)
            df['Date'] = pd.to_datetime(df['Date'])

            df_indexed = df.set_index('Date')
            for date, night in self.nights.items():
                pandas_date = pd.to_datetime(date)
                if pandas_date in df_indexed.index:
                    night.demand = int(df_indexed.loc[pandas_date]["Unconstrained Demand"])
                    

            return df
    
    def rates(self, password, forecasting_days, bob_df):
        if password == self.password and bob_df is not None:
            variable_cost = 30
            historical_adr_weight = 0.5
            today = datetime.now().date()
            market_segment_discounts = {"Corporate": 0.25, 'Online TA': 0.20, 'Retail': 0, "Offline TA/TO": 0.3}
            bid_prices_calculated = {} # To store bid prices temporarily

            rates_df = bob_df.copy()
            if 'Date' in rates_df.columns:
                rates_df['Date'] = pd.to_datetime(rates_df['Date']).dt.date
                rates_df = rates_df.set_index('Date')
            else:
                print("DEBUG RATES - Warning: 'Date' column not found in bob_df for setting index.")
                return

            for i in range(forecasting_days):
                current_date = today + timedelta(days=i)
                is_night_present = current_date in self.nights
                is_date_in_df = current_date in rates_df.index

                if is_night_present and is_date_in_df:
                    night = self.nights[current_date]
                    remaining_demand = night.demand
                    remaining_supply = night.occupied
                    current_adr = night.calculate_adr()
                    elasticity = night.get_base_elasticity()
                    historical_adr = self.get_historical_adr_for_night(current_date, (current_date - today).days, "Retail")
                    avg_historical_adr = np.mean(historical_adr) if historical_adr else current_adr

                    if remaining_supply > 0 and remaining_demand > 0:
                        alpha = remaining_demand / remaining_supply if remaining_supply > 0 else 0
                        price_elasticity = (elasticity * variable_cost) / (elasticity + 1) * alpha
                        suggested_rate_elasticity = price_elasticity
                        night.optimized_rate = max(variable_cost + 1, (suggested_rate_elasticity * (1 - historical_adr_weight)) + (avg_historical_adr * historical_adr_weight))
                        

                    elif remaining_supply > 0:
                        night.optimized_rate = max(variable_cost + 1, current_adr * 0.95)
                        print(f"DEBUG RATES (Supply > 0) - Date: {current_date}, Optimized Rate: {night.optimized_rate}, Current ADR: {current_adr}")
                    else:
                        night.optimized_rate = current_adr
                        print(f"DEBUG RATES (No Supply) - Date: {current_date}, Optimized Rate: {night.optimized_rate}, Current ADR: {current_adr}")

                    

                    # Calculate Bid Prices Immediately After Rate Optimization
                    if night.optimized_rate > 0 and night.demand is not None:
                        bid_price = night.calculate_bid_prices()
                        night.bidprice = bid_price
                        bid_prices_calculated[current_date] = bid_price
                        
                    else:
                        print(f"DEBUG RATES - Skipping Bid Price calculation for {current_date} due to zero optimized rate or no demand.")
                else:
                    print(f"DEBUG RATES - Skipping date: {current_date} (Night not present or date not in df).")

            return bid_prices_calculated # Return the calculated bid prices
        else:
            print("DEBUG RATES - Password does NOT match or bob_df is None")
            return {}
            
