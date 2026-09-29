import os
import getpass
import mysql.connector
from tkinter import *

db_password = os.getenv("BBMS_DB_PASSWORD") or getpass.getpass("MySQL password: ")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abcd",
    database="bbms",
)
cursor = db.cursor()

# ---------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------
main_root = Tk()
main_root.title("BLOOD BANK")
main_root.geometry("800x600")
main_root.configure(background="brown")

Label(main_root, text="BLOOD BANK SYSTEM", font=("Helvetica", 18, "bold"), bg="white").pack(pady=20)


# ---------------------------------------------------------------
# Database functions
# ---------------------------------------------------------------

def insert_donor(name, age, gender, address, contactno):
    """Insert a donor and return the new donor's ID (or None on failure)."""
    try:
        query = "INSERT INTO donors (name, age, gender, address, contactno) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (name, age, gender, address, contactno))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        db.rollback()
        print("Error inserting donor:", e)
        return None


def donor_exists(donor_id):
    try:
        cursor.execute("SELECT 1 FROM donors WHERE id = %s", (donor_id,))
        return cursor.fetchone() is not None
    except Exception as e:
        print("Error checking donor:", e)
        return False


def insert_blood(donor_id, bloodgroup, platelet, rbc):
    try:
        query = ("INSERT INTO blood (donor_id, bloodgroup, platelet, rbc, date) "
                 "VALUES (%s, %s, %s, %s, CURDATE())")
        cursor.execute(query, (donor_id, bloodgroup, platelet, rbc))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print("Error inserting blood:", e)
        return False


def retrieve(bg):
    try:
        query = """SELECT donors.id, donors.name, donors.age, donors.gender, donors.address, donors.contactno,
                          blood.bloodgroup, blood.platelet, blood.rbc, blood.date
                   FROM donors INNER JOIN blood ON donors.id = blood.donor_id
                   WHERE blood.bloodgroup = %s"""
        cursor.execute(query, (bg,))
        return cursor.fetchall()
    except Exception as e:
        print("Error retrieving data:", e)
        return []


# ---------------------------------------------------------------
# Windows
# ---------------------------------------------------------------
BG = "#FF8F8F"


def donor_details_window():
    window = Toplevel(main_root)
    window.title("Donor Details")
    window.geometry("400x350")
    window.configure(background=BG)

    Label(window, text="Name:", font=("Helvetica", 12), bg=BG).place(x=20, y=20)
    name_entry = Entry(window)
    name_entry.place(x=130, y=20)

    Label(window, text="Age:", font=("Helvetica", 12), bg=BG).place(x=20, y=60)
    age_entry = Entry(window)
    age_entry.place(x=130, y=60)

    Label(window, text="Gender:", font=("Helvetica", 12), bg=BG).place(x=20, y=100)
    gender_var = StringVar(value="Male")
    Radiobutton(window, text="Male", variable=gender_var, value="Male", bg=BG).place(x=130, y=100)
    Radiobutton(window, text="Female", variable=gender_var, value="Female", bg=BG).place(x=190, y=100)
    Radiobutton(window, text="Other", variable=gender_var, value="Other", bg=BG).place(x=270, y=100)

    Label(window, text="Address:", font=("Helvetica", 12), bg=BG).place(x=20, y=140)
    address_entry = Entry(window)
    address_entry.place(x=130, y=140)

    Label(window, text="Contact:", font=("Helvetica", 12), bg=BG).place(x=20, y=180)
    contact_entry = Entry(window)
    contact_entry.place(x=130, y=180)

    # One status label that gets updated (instead of stacking new labels)
    status = Label(window, text="", bg=BG, font=("Helvetica", 10, "bold"))
    status.place(x=20, y=220)

    def submit():
        name = name_entry.get().strip()
        age = age_entry.get().strip()
        gender = gender_var.get()
        address = address_entry.get().strip()
        contact = contact_entry.get().strip()

        if name and age.isdigit() and contact:
            new_id = insert_donor(name, age, gender, address, contact)
            if new_id:
                status.config(text=f"Donor added! Donor ID: {new_id}  (note this down)", fg="green")
                for e in (name_entry, age_entry, address_entry, contact_entry):
                    e.delete(0, END)
            else:
                status.config(text="Failed to add donor.", fg="red")
        else:
            status.config(text="Enter valid data!", fg="red")

    Button(window, text="Submit", command=submit).place(x=130, y=260)
    Button(window, text="Close", command=window.destroy).place(x=210, y=260)


def blood_details_window():
    window = Toplevel(main_root)
    window.title("Blood Details")
    window.geometry("560x300")
    window.configure(background=BG)

    Label(window, text="Donor ID:", font=("Helvetica", 12), bg=BG).place(x=20, y=20)
    donor_id_entry = Entry(window)
    donor_id_entry.place(x=320, y=20)

    Label(window, text="Blood Group:", font=("Helvetica", 12), bg=BG).place(x=20, y=60)
    bg_entry = Entry(window)
    bg_entry.place(x=320, y=60)

    Label(window, text="Platelet count (hundreds of thousands):", font=("Helvetica", 12), bg=BG).place(x=20, y=100)
    platelet_entry = Entry(window)
    platelet_entry.place(x=320, y=100)

    Label(window, text="RBC count (millions):", font=("Helvetica", 12), bg=BG).place(x=20, y=140)
    rbc_entry = Entry(window)
    rbc_entry.place(x=320, y=140)

    status = Label(window, text="", bg=BG, font=("Helvetica", 10, "bold"))
    status.place(x=20, y=180)

    def is_number(s):
        return s.replace(".", "", 1).isdigit()

    def submit():
        donor_id = donor_id_entry.get().strip()
        blood_group = bg_entry.get().strip().upper()
        platelet = platelet_entry.get().strip()
        rbc = rbc_entry.get().strip()

        if not (donor_id.isdigit() and blood_group and is_number(platelet) and is_number(rbc)):
            status.config(text="Enter valid data!", fg="red")
            return

        if not donor_exists(int(donor_id)):
            status.config(text=f"No donor found with ID {donor_id}.", fg="red")
            return

        if insert_blood(int(donor_id), blood_group, platelet, rbc):
            status.config(text="Blood details added successfully!", fg="green")
            for e in (donor_id_entry, bg_entry, platelet_entry, rbc_entry):
                e.delete(0, END)
        else:
            status.config(text="Failed to add blood details.", fg="red")

    Button(window, text="Submit", command=submit).place(x=320, y=220)
    Button(window, text="Close", command=window.destroy).place(x=400, y=220)


def request_blood_window():
    window = Toplevel(main_root)
    window.title("Request Blood")
    window.geometry("400x250")
    window.configure(background=BG)

    Label(window, text="Enter Blood Group to Search:", font=("Helvetica", 12), bg=BG).place(x=20, y=20)
    bg_entry = Entry(window)
    bg_entry.place(x=220, y=20)

    status = Label(window, text="", bg=BG, fg="red")
    status.place(x=20, y=100)

    def search():
        bg = bg_entry.get().strip().upper()
        if bg:
            status.config(text="")
            display_matching_donors(bg)
        else:
            status.config(text="Please enter a blood group.")

    Button(window, text="Search", command=search).place(x=220, y=60)
    Button(window, text="Close", command=window.destroy).place(x=280, y=60)


def display_matching_donors(bg):
    data = retrieve(bg)
    if not data:
        popup = Toplevel(main_root)
        popup.title("No Matches")
        Label(popup, text=f"No donors found for blood group {bg}", fg="red").pack(padx=20, pady=20)
        Button(popup, text="Close", command=popup.destroy).pack(pady=10)
        return

    window = Toplevel(main_root)
    window.title(f"Donors with blood group {bg}")
    window.geometry("900x400")

    headers = ["ID", "Name", "Age", "Gender", "Address", "Contact", "Blood Group", "Platelet", "RBC", "Date"]
    for col, header in enumerate(headers):
        Label(window, text=header, font=("Arial", 10, "bold"), borderwidth=1, relief="solid").grid(
            row=0, column=col, sticky="nsew")

    for row_idx, row in enumerate(data, start=1):
        for col_idx, val in enumerate(row):
            Label(window, text=val, borderwidth=1, relief="solid").grid(
                row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)


# ---------------------------------------------------------------
# Buttons on main window
# ---------------------------------------------------------------
Button(main_root, text="Donor Details", width=20, command=donor_details_window).pack(pady=10)
Button(main_root, text="Blood Details", width=20, command=blood_details_window).pack(pady=10)
Button(main_root, text="Request Blood", width=20, command=request_blood_window).pack(pady=10)
Button(main_root, text="Exit", width=20, command=main_root.destroy).pack(pady=10)

main_root.mainloop()
