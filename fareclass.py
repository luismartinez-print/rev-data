import streamlit as st

class FareClass():
    def __init__(self, name, code, min_rate, max_rate):
        self.name = name
        self.code = code
        self.min_rate = min_rate
        self.max_rate = max_rate
    
    def chanage_min(self, min_rate):
        if min_rate < 0:
            st.write("You cannot set a fare limit as negative")
        if min_rate != self.min_rate:
            self.min_rate = min_rate
    
    def change_max(self, max_rate):
        if max_rate < 0 | max_rate < self.min_rate:
            st.write("The max rate cannot be lower than 0 or the minum rate")
        if max_rate != self.max_rate:
            self.max_rate = max_rate
        ### ADD more methods to the fare class thingy####

    def show(self):
        st.write(f"{self.name} {self.code}")