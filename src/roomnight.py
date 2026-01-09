import streamlit as st
from src.room import Room
from datetime import date

class RoomNight():
    def __init__(self, room_id, is_sold, fare_class , rate, los, dba):
        self.room_id = room_id
        self.is_sold = is_sold
        self.fare_class = fare_class #Market Segment
        self.rate = rate
        self.los = los
        self.dba = dba
    
    #### Some cool methodds that RoomNight might need ####

    def show(self):
        st.write(f"{self.is_sold} {self.rate} {self.fare_class} {self.dba}")
    

