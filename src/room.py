import streamlit as st


class Room():
    def __init__(self, room_id, room_tpye):
        self.room_id = room_id
        self.room_type = room_tpye
        self.varaible_cost = 50
    
    ##### SOME METHODS HERE FOR ROOM #####
    
    def show(self):
        st.write(f"Room {self.room_id} of type {self.room_type}")

