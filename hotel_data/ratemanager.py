import streamlit as st
from datetime import timedelta, datetime
import pandas as pd
import numpy as np

class RateManager():
    def __init__(self):
        self.default_elasticity = -1.5
        self.variable_cost_per_room = 50
        self.historical_adr_weight = 0.3

    def optimize_rates(self, book, bob_df: pd.DataFrame):
        optimized_rates = {}

        for index, row in bob_df.iterrows():
            date = row["Date"].date()
            dba = (date - datetime.today().date()).days
            if dba < 0:
                continue
            remaining_demand = row['Remaining Demand']
            remaining_supply = row['Available Rooms']  # Corrected key
            total_rooms = row['Total Rooms']
            current_adr = row['ADR'] if pd.notna(row['ADR']) and row['Total Occupied'] > 0 else self.get_current_average_rate(book, date) # Using 'Total Occupied'

            elasticity = self.get_dynamic_elasticity(date)

            if remaining_supply > 0 and remaining_demand > 0:
                alpha = remaining_demand / remaining_supply if remaining_supply > 0 else 0
                price_elasticity = (elasticity * self.variable_cost_per_room) / (elasticity + 1) * alpha
                suggested_rate_elasticity = price_elasticity

                historical_adr = self.get_historical_adr(book, date, dba)
                avg_historical_adr = np.mean(historical_adr) if historical_adr else current_adr

                suggested_rate = (suggested_rate_elasticity * (1 - self.historical_adr_weight)) + (avg_historical_adr * self.historical_adr_weight)
                optimized_rates[date] = max(self.variable_cost_per_room + 1, suggested_rate)
            elif remaining_supply > 0:
                optimized_rates[date] = max(self.variable_cost_per_room + 1, current_adr * 0.95)
            else:
                optimized_rates[date] = current_adr

        self.apply_optimized_rates(book, optimized_rates)

    def get_dynamic_elasticity(self, date):
        day_of_week = date.weekday()  # Monday is 0, Sunday is 6
        month = date.month

        elasticity = self.default_elasticity

        if day_of_week >= 5:  # Weekend
            elasticity -= 0.2
        elif month in [12, 1, 2, 3]:  # High season (example)
            elasticity -= 0.1
        elif month in [6, 7, 8]:  # Mid season (example)
            elasticity -= 0.05

        return elasticity

    def get_historical_adr(self, book, future_date, dba):
        historical_adrs = []
        future_dow = future_date.weekday()
        today = datetime.today().date()
        future_dba = (future_date - today).days
        for hist_date, hist_night in book.nights.items():
            if hist_date < today and hist_date.weekday() == future_dow:
                hist_dba = (hist_date - (today - timedelta(days=future_dba))).days
                if abs(hist_dba) <= 3 and hist_night.calculate_adr() > 0:
                    historical_adrs.append(hist_night.calculate_adr())
        return historical_adrs

    def get_current_average_rate(self, book, date):
        if date in book.nights and book.nights[date].roomnights and book.nights[date].occupied_rooms() > 0:
            return book.nights[date].calculate_adr()
        else:
            return 100

    def apply_optimized_rates(self, book, optimized_rates):
        for date, rate in optimized_rates.items():
            if date in book.nights:
                for rn in book.nights[date].roomnights:
                    if not rn.is_sold:
                        rn.rate = rate