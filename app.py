from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('welcome.html')

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="VRM"
)

cursor = db.cursor()

@app.route('/give-to-rent', methods=['GET', 'POST'])
def give_to_rent():
    if request.method == 'POST':
        vehicle_no = request.form['vehicle_no']
        owner_name = request.form['owner_name']
        vehicle_type = request.form['vehicle_type']
        vehicle_company = request.form['vehicle_company']
        model = request.form['model']
        rent = request.form['rent']
        admin_dob = request.form['admin_dob']

        # Insert the vehicle data into the vehicle table
        cursor.execute('''INSERT INTO vehicle (vehicle_no, owner_name, vehicle_type, 
                        vehicle_company, model, rent, available, admin_dob) 
                        VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s)''', 
                        (vehicle_no, owner_name, vehicle_type, vehicle_company, model, rent, admin_dob))
        db.commit()

        return redirect('/')
    return render_template('give_to_rent.html')

@app.route('/rent-vehicle')
def rent_vehicle():
    cursor.execute("SELECT * FROM vehicle WHERE available = TRUE")
    vehicles = cursor.fetchall()
    return render_template('rent_vehicle.html', vehicles=vehicles)

@app.route('/rent/<int:vehicle_no>', methods=['GET', 'POST'])
def rent(vehicle_no):
    cursor.execute("SELECT * FROM vehicle WHERE vehicle_no = %s", (vehicle_no,))
    vehicle = cursor.fetchone()

    if request.method == 'POST':
        renter_name = request.form['renter_name']
        renter_age = request.form['renter_age']
        renter_gender = request.form['renter_gender']
        start_time = datetime.now()

        # Insert the rental details into the rentals table
        cursor.execute('''INSERT INTO rentals (vehicle_no, renter_name, renter_age, 
                        renter_gender, start_time, end_time, amount_paid) 
                        VALUES (%s, %s, %s, %s, %s, NULL, 0)''', 
                        (vehicle_no, renter_name, renter_age, renter_gender, start_time))
        rental_id = cursor.lastrowid
        db.commit()

        # Update vehicle availability
        cursor.execute("UPDATE vehicle SET available = FALSE WHERE vehicle_no = %s", (vehicle_no,))
        db.commit()

        return render_template('rental_confirmation.html', rental_id=rental_id , vehicle=vehicle, renter_name=renter_name, renter_age=renter_age, renter_gender=renter_gender, start_time=start_time)
    return render_template('rent_form.html', vehicle=vehicle)

@app.route('/return-vehicle', methods=['GET', 'POST'])
def return_vehicle():
    if request.method == 'POST':
        rental_id = request.form['rental_id']
        cursor.execute("""
            SELECT rentals.*, vehicle.rent 
            FROM rentals 
            JOIN vehicle ON rentals.vehicle_no = vehicle.vehicle_no 
            WHERE rental_id = %s AND end_time IS NULL
        """, (rental_id,))
        rental = cursor.fetchone()

        if rental:
            start_time = rental[5]
            end_time = datetime.now()
            rental_duration = (end_time - start_time).total_seconds() / 3600

            vehicle_rent = float(rental[9])
            rent_per_hour = vehicle_rent / 24
            amount_due = rent_per_hour * rental_duration

            cursor.execute("""
                UPDATE rentals 
                SET end_time = %s, amount_paid = %s, paid = TRUE 
                WHERE rental_id = %s
            """, (end_time, amount_due, rental_id))
            db.commit()

            cursor.execute("UPDATE vehicle SET available = TRUE WHERE vehicle_no = %s", (rental[1],))
            db.commit()

            return render_template('return_vehicle.html', amount_due=round(amount_due, 2))

        else:
            return "Rental ID not found or vehicle already returned."

    return render_template('return_vehicle.html')



@app.route('/delete-vehicle', methods=['GET', 'POST'])
def delete_vehicle():
    message = None
    if request.method == 'POST':
        vehicle_no = request.form['vehicle_no']

        cursor.execute("SELECT * FROM vehicle WHERE vehicle_no = %s", (vehicle_no,))
        vehicle = cursor.fetchone()

        if not vehicle:
            message = f"Vehicle {vehicle_no} not found."
        else:
            cursor.execute("UPDATE vehicle SET available = FALSE WHERE vehicle_no = %s", (vehicle_no,))
            db.commit()
            message = f"Vehicle {vehicle_no} has been deleted (a)"

        return render_template('delete_vehicle.html', message=message)

    return render_template('delete_vehicle.html')

if __name__ == '__main__':
    app.run(debug=True)
