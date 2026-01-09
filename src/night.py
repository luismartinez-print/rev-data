import streamlit as st 
from src.roomnight import RoomNight
from datetime import date
import pandas as pd
import numpy as np
import pulp

class Night():
    def __init__(self, date):
        self.date = date
        self.roomnights = []
        self.weekday = date.weekday()
        self.month = date.month

        self.historical_mix = {}
        self.capacity = 0
        self.occupied = 0
        self.occupancy = 0.0
        self.group = 0
        self.transient = 0
        self.adr = 0.0
        self.demand = 0
        self.reveune = 0
        self.occupancy_rate = 0.0
        self.revpar = 0.0
        self.available_rooms = 0
        self.elasticity = self.get_base_elasticity()
        self.optimized_rate = 0.0
        self.bidprice = 0.0


    def append_live_reservations(self, df: pd.DataFrame, rooms: dict):
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        night_df = df[df['Date'] == self.date]

        added_rooms = set()

        for _, row in night_df.iterrows():
            room_id = row['Room Id']
            if room_id in rooms and room_id not in added_rooms:
                room = rooms[room_id]
                is_sold = int(row.get('is_sold', 0))
                fare_class = row.get('Market Segment', None)
                rate = float(row.get('Rate', 0.0))
                los = int(row.get('LOS', 0))
                booking_date_raw = row.get('Booking Date', None)
                if pd.notna(booking_date_raw):
                    booking_date = pd.to_datetime(booking_date_raw).date()
                    dba = (self.date - booking_date).days
                else:
                    dba = None
                rn = RoomNight(room, is_sold, fare_class, rate, los, dba)
                self.roomnights.append(rn)
            
                added_rooms.add(room_id)
            else:
                None
                

    def create_roomnight(self, df: pd.DataFrame, rooms: dict):
        self.roomnights = []
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        night_df = df[df['Date'] == self.date]

        added_rooms = set()

        for _, row in night_df.iterrows():
            room_id = str(row['Room Id'])
            if room_id in rooms and room_id not in added_rooms:
                room = rooms[room_id]
            
                is_sold = int(row.get('is_sold', 0))
                fare_class = row.get('Market Segment', None)
                rate = float(row.get('Rate', 0.0))
                los = int(row.get('LOS', 0))
                dba_raw = row.get("DBA")
                dba = None
                if pd.notna(dba_raw):
                    dba = int(dba_raw)
                rn = RoomNight(room, is_sold, fare_class, rate, los, dba)
                self.roomnights.append(rn)
                added_rooms.add(room_id)
            else:
                st.write("What the hell")

    def total_rooms(self):
        if len(self.roomnights) > 0:
            total_rooms = len(self.roomnights)
            self.capacity = total_rooms
            return total_rooms
    
    def occupied_rooms(self):
        sold_rooms = [room for room in self.roomnights if room.is_sold == 1]
        occupied = len(sold_rooms)
        self.occupied = occupied
        return occupied
    
    def group_occupied(self):
        sold_rooms = [room for room in self.roomnights if room.is_sold == 1 and room.fare_class == 'Group']
        group = len(sold_rooms)
        self.group = group
        return group

    def transient_occupied(self):
        sold_rooms = [room for room in self.roomnights if room.is_sold == 1 and room.fare_class != 'Group']
        transient = len(sold_rooms)
        self.transient = transient
        return transient
    
    def total_revenue(self):
        revenue = sum(room.rate for room in self.roomnights if room.is_sold == 1)
        self.revenue = revenue
        return revenue
    
    def calculate_occupancy(self):
        total_rooms = self.total_rooms()
        sold = self.occupied_rooms()
        occupancy = sold / total_rooms
        self.occupancy = occupancy
        return occupancy
    
    def calculate_adr(self):
        sold = self.occupied_rooms()
        adr = self.total_revenue() / sold
        adr = round(adr, 2)
        self.adr = adr
        return adr
    
    def calculate_revpar(self):
        total = self.total_rooms()
        revpar = self.total_revenue() / total if total > 0 else 0
        self.revpar = revpar
        return revpar
    
    def calculate_available_rooms(self):
        available_rooms = self.total_rooms() - self.occupied_rooms()
        self.available_rooms = available_rooms
        return available_rooms
    
    def get_booking_curve(self):
        booking_curve = {}
        for roomnight in self.roomnights:
            dba = roomnight.dba
            if dba > 28:
                days_before = '28+ Days Before Arrival'
            elif dba > 21:
                days_before = '22 - 28 Days Before Arrival'
            elif dba > 14:
                days_before = '15 - 21 Days Before Arrival'
            elif dba > 7:
                days_before = '8 - 14 Days Before Arrival'
            elif dba > 3:
                days_before = '4-7 Days Before'
            elif dba > 1:
                days_before = '2-3 Days Before'
            elif dba == 1:
                days_before = '1 Day Before'
            elif dba == 0:
                days_before = 'Arrival Day'
        
            if days_before not in booking_curve:
                booking_curve[days_before] = 0
            booking_curve[days_before] += 1
        return booking_curve

    
    def get_base_elasticity(self):
        weekday = self.date.weekday()  # Monday is 0, Sunday is 6
        if weekday >= 5:
            return -2.0
        else:
            return -1.5
    

    def calculate_demand_mix(self):
        fare_class_count = {}
        total_non_group_roomnights = 0
        for rn in self.roomnights:
            if rn.fare_class and rn.fare_class != "Group":
                fare_class_count[rn.fare_class] = fare_class_count.get(rn.fare_class, 0) + 1
                total_non_group_roomnights += 1
        
        historical_mix = {}
        if total_non_group_roomnights > 0:
            for fc, count in fare_class_count.items():
                historical_mix[fc] = count / total_non_group_roomnights
        else:
            print("Here is the prob")
        self.historical_mix = historical_mix


        return historical_mix
    
    def calculate_bid_prices(self):
        bid_price = 0.0
        historical_mix = self.calculate_demand_mix()
        if self.demand > 0 and self.optimized_rate > 0 and historical_mix and self.available_rooms > 0:
            # Define explicit coefficients (for debugging)
            coefficients = {
                "Online TA": 0.8 * self.optimized_rate,  # Example: 20% discount
                "Corporate": 0.75 * self.optimized_rate, # Example: 25% discount
                "Offline TA/TO": 0.7 * self.optimized_rate, # Example: 30% discount
                "Retail": self.optimized_rate
            }
            print("DEBUG NIGHT - Explicit Coefficients:", coefficients)

            # Define explicit demand constraints (for debugging)
            demand_constraints = {
                "Online TA": int(self.demand * historical_mix.get("Online TA", 0.2)), # Example proportion
                "Corporate": int(self.demand * historical_mix.get("Corporate", 0.2)),
                "Offline TA/TO": int(self.demand * historical_mix.get("Offline TA/TO", 0.3)),
                "Retail": int(self.demand * historical_mix.get("Retail", 0.3))
            }
            print("DEBUG NIGHT - Explicit Demand Constraints:", demand_constraints)

            # Total capacity
            total_capacity = self.available_rooms
            print("DEBUG NIGHT - Total Capacity:", total_capacity)

            # Create decision variables for each segment
            decision_vars = {seg: pulp.LpVariable(name=seg, lowBound=0, cat="Continuous") for seg in coefficients}
            print(f"DEBUG NIGHT - Segment Variables: {decision_vars}")

            # Define the LP problem
            model = pulp.LpProblem("Bid_Price_Calculation", pulp.LpMaximize)

            # Objective function: Maximize total revenue
            model += pulp.lpSum(coefficients[seg] * decision_vars[seg] for seg in coefficients), "Total_Revenue"

            # Capacity constraint
            model += pulp.lpSum(decision_vars[seg] for seg in coefficients) <= total_capacity, "Total_Capacity"

            # Individual demand constraints
            for seg in demand_constraints:
                model += decision_vars[seg] <= demand_constraints[seg], f"Demand_Constraint_{seg}"

            # Solve the model
            model.solve(pulp.PULP_CBC_CMD(msg=False))
            print(f"DEBUG NIGHT - Date: {self.date}")

            # Extract the shadow price of the capacity constraint
            capacity_constraint = model.constraints.get("Total_Capacity")
            if capacity_constraint:
                bid_price = capacity_constraint.pi
                print(f"DEBUG NIGHT - Date: {self.date}, Capacity Constraint Shadow Price: {bid_price}")
            else:
                print(f"DEBUG NIGHT - Date: {self.date}, Capacity Constraint NOT found or LP not Optimal.")

        self.bidprice = bid_price
        return bid_price


    def show_roomnights(self):
        for room in self.roomnights:
            room.show()

    def show_booking_curve(self, dba):
        occupied = self.occupied_rooms()
        up_to_dba = []
        for rn in self.roomnights:
            if rn.dba is not None and dba <= rn.dba:
                up_to_dba.append(rn)
        relative_booking = len(up_to_dba)
        
        relative_curve = relative_booking / occupied if occupied > 0 else 1
        return relative_curve
    
    def show(self):
        st.write(f"{self.date} | {self.weekday} | {self.demand}")