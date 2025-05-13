import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
import streamlit as st

class LiveReservaitonGenerator():
    def __init__(self, fare_classes, market_segments, num_hotels=1, rooms_per_hotel=30):
        self.fare_classes = fare_classes
        self.market_segments = market_segments
        self.num_hotels = num_hotels
        self.rooms_per_hotel = rooms_per_hotel
        self.room_ids = [f"{hotel_id * rooms_per_hotel + room_num + 101}"
                         for hotel_id in range(num_hotels)
                         for room_num in range(rooms_per_hotel)]
        self.booking_probability = 0.30 # Base booking probability




    def _generate_booking_probability(self, arrival_date, dba):
        """Calculates booking probability with DBA, day of week, and seasonality."""      

              
        base_prob = 0.20  # Lower base
        pickup = 0.60 * np.exp(-abs(dba) / 0.05) 

        wday = arrival_date.weekday()  # Monday is 0, Sunday is 6
        weekday_adjust = 0
        if wday == 2:
            weekday_adjust = 0.10
        if wday == 1:
            weekday_adjust = 0.15
        if wday == 3:  # Thursday
            weekday_adjust = 0.20
        elif wday == 4:  # Friday
            weekday_adjust = 0.20
        elif wday in [5, 6]:  # Saturday, Sunday
            weekday_adjust = 0.08

        seasonal = 0
        month = arrival_date.month
        if month in [12, 1, 2]:
            seasonal = 0.20
        elif month in [3, 4, 9, 10]:
            seasonal = 0.10
        elif month in [6, 7, 8]:
            seasonal = 0.15

        probability = base_prob + pickup + weekday_adjust + seasonal
        return np.clip(probability, 0, 0.95) # Increased clip

    def generate_next_reservations(self, forecast_days, existing_room_nights=None):
        live_reservations = []
        occupied_rooms = {}
        today = datetime.now().date()
        end_date = today + timedelta(days=forecast_days)

        if existing_room_nights:
            for rn in existing_room_nights:
                arrival_date = rn.date
                room_id = rn.room.room_id
                for day in range(rn.los):
                    stay_date = arrival_date + timedelta(days=day)
                    if stay_date <= end_date:
                        if stay_date not in occupied_rooms:
                            occupied_rooms[stay_date] = set()
                        occupied_rooms[stay_date].add(room_id)

        for i in range(forecast_days):
            current_date = today + timedelta(days=i)

            for room_id in self.room_ids:
                if room_id in occupied_rooms.get(current_date, set()):
                    continue

                max_booking_lead_time = 90
                booking_lead_time = random.randint(0, max_booking_lead_time)
                potential_booking_date = today - timedelta(days=booking_lead_time)
                dba_potential = (current_date - potential_booking_date).days

                booking_probability = self._generate_booking_probability(current_date, dba_potential)

                if random.random() < booking_probability:
                    is_sold = 1
                    market_segment = random.choice(self.market_segments)
                    fare_class_data = self.fare_classes.get(market_segment, random.choice(list(self.fare_classes.values())))
                    if fare_class_data:
                        min_rate = fare_class_data.min_rate * 2 # Increased min rate
                        max_rate = fare_class_data.max_rate * 1.8 # Increased max rate
                        scale = abs(max_rate - min_rate) / 4
                        rate = round(np.clip(np.random.normal((min_rate + max_rate) / 2, scale), min_rate, max_rate), 0)
                        los = random.randint(1, 5)
                        booking_date = potential_booking_date
                        dba = dba_potential

                        for day in range(los):
                            stay_date = current_date + timedelta(days=day)
                            if stay_date <= end_date:
                                if stay_date not in occupied_rooms:
                                    occupied_rooms[stay_date] = set()
                                occupied_rooms[stay_date].add(room_id)
                                live_reservations.append({
                                    'Date': stay_date.strftime('%Y-%m-%d'),
                                    'Room Id': room_id,
                                    'is_sold': 1,
                                    'Market Segment': market_segment,
                                    'Rate': rate,
                                    'LOS': los,
                                    'Booking Date': booking_date.strftime('%Y-%m-%d'),
                                    'DBA': (stay_date - booking_date).days
                                })
                                
                else:
                    live_reservations.append({
                        'Date': current_date.strftime('%Y-%m-%d'),
                        'Room Id': room_id,
                        'is_sold': 0,
                        'Market Segment': None,
                        'Rate': 0,
                        'LOS': 0,
                        'Booking Date': None,
                        'DBA': None
                    })



        return pd.DataFrame(live_reservations)