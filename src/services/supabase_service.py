from supabase import create_client, Client
import os
from typing import Dict
import bcrypt
from src.models.book import Book

#Initialize Supbase Client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Supabase url and key must be set as environment variables"
    )
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_all_books() -> Dict[int, Book]:
    #Loads all the books as a dict as a dictionary with key of book num and value of book object
    #Input -> none, when app initialized
    #Out put -> Dict[int, book] a dicionary of book num and book object
    try:
        response = supabase.table("books").select("*").execute()
        if response.error:
            print(f"Error Loading books: {response.error}")
            return {}
        books_data = response.data
        books = {}
        for book_data in books_data:
            book_number = book_data['book_number']
            name = book_data['name']
            password = book_data['password']
            books[book_number] = Book(name=name, password=password)
        
        return books
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}
    
def create_book(name: str, password: str) -> int | None:
    #Creates a new book in the supabase database
    # args -> name and password for given book
    # output -> int(the new book number unique identifier)
    try:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        response = (
            supabase.table("books")
            .instert({"name": name, "password": hashed_password})
            .execute()
        )
        if response.error:
            print(f"Error Creating Book {response.error}")
            return None
        new_book_number = response.data[0]['book_number']
        return new_book_number
    except Exception as e:
        print(f"Unexpected error occurred {e}")
        return None