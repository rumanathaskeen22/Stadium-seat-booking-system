import datetime
import os
import random

from flask import Flask, render_template, request, redirect, session

import pymongo
from bson import ObjectId

from Mail import send_email

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static"


myClient = pymongo.MongoClient('mongodb://localhost:27017/')
mydb = myClient["StadiumTicketBookingSystem"]
game_organiser_col = mydb["GameOrganiser"]
stadium_col = mydb["Stadium"]
time_slot_col = mydb["TimeSlots"]
schedule_col = mydb["Schedule"]
audience_col = mydb["Audience"]
ticket_col = mydb["Tickets"]
booking_col = mydb["Bookings"]



app = Flask(__name__)
app.secret_key = "StadiumTicketBookingSystem"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/adminLoginPage")
def adminLoginPage():
    return render_template("adminLoginPage.html")

@app.route("/organiserLoginPage")
def organiserLoginPage():
    return render_template("organiserLoginPage.html")

@app.route("/audianLoginPage")
def audianLoginPage():
    return render_template("audianLoginPage.html")


@app.route("/aLogin1",methods=['post'])
def aLogin1():
    Username = request.form.get("Username")
    password = request.form.get("password")
    if Username == 'admin' and password == 'admin':
        session['role'] = 'admin'
        return render_template("adminHome.html")
    elif Username != 'admin':
        return render_template("message.html",msg='Invalid UserName "'+Username+'"',color='text-danger')
    elif password != 'admin':
        return render_template("message.html",msg='Invalid password "'+password+'"',color='text-danger')


@app.route("/adminHome")
def adminHome():
    return render_template("adminHome.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/organiserReg")
def organiserReg():
    return render_template("organiserReg.html")


@app.route("/organiserReg1",methods=['post'])
def organiserReg1():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    picture = request.files.get("picture")
    address = request.form.get("address")
    path = APP_ROOT + "/Pictures/" + picture.filename
    picture.save(path)
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = game_organiser_col.count_documents(query)
    if count == 0:
        game_organiser_col.insert_one({"name":name,"email":email,"phone": phone, "password": password,"picture":picture.filename,"address":address,"account_status":'Not Activated'})
        return render_template("message.html", msg='Organiser Registered Successfully', color='text-success')
    else:
        return render_template("message.html",msg='Duplicate Organiser Details',color='text-danger')

@app.route("/viewOrganisers")
def viewOrganisers():
    game_organisers = game_organiser_col.find()
    return render_template("viewOrganisers.html",game_organisers=game_organisers)


@app.route("/authorize_organiser")
def authorize_organiser():
    gameOrganiser_id = request.args.get("gameOrganiser_id")
    game_organiser = game_organiser_col.find_one({'_id':ObjectId(gameOrganiser_id)})
    query = {}
    if game_organiser['account_status'] == 'Not Activated':
        query = {"$set":{"account_status":'Activated'}}
    else:
        query = {"$set": {"account_status": 'Not Activated'}}
    game_organiser_col.update_one({'_id':ObjectId(gameOrganiser_id)},query)
    return viewOrganisers()

@app.route("/organiserLoginPage1",methods=['post'])
def organiserLoginPage1():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email":email,"password":password}
    total_count = game_organiser_col.count_documents(query)
    if total_count > 0:
        results = game_organiser_col.find(query)
        for result in results:
            if result['account_status'] == 'Activated':
                        session['gameOrganiser_id'] = str(result['_id'])
                        session['role'] = "gameOrganiser"
                        return redirect("/gameOrganiserHome")
            else:
                return render_template("message.html", msg="Your Account Not Verified", color='text-warning')
    else:
        return render_template("message.html", msg="Invalid login details", color='text-danger')

@app.route("/gameOrganiserHome")
def gameOrganiserHome():
    organiser = game_organiser_col.find_one({"_id":ObjectId(session['gameOrganiser_id'])})
    return render_template("gameOrganiserHome.html",organiser=organiser)

@app.route("/addStadium")
def addStadium():
    return render_template("addStadium.html")


@app.route("/addStadium1",methods=['post'])
def addStadium1():
    stadium_name = request.form.get("stadium_name")
    # stadium_type = request.form.get("stadium_type")
    location = request.form.get("location")
    address = request.form.get("address")
    query = {}
    count = stadium_col.count_documents(query)
    if count == 0:
        stadium_col.insert_one({"stadium_name":stadium_name,"location":location,"address":address,"status":'Available'})
        return render_template("message.html", msg='Stadium Added', color='text-success')
    else:
        return render_template("message.html", msg='You Cant Add Stadium,Only One Stadium', color='text-danger')


@app.route("/viewStadiums")
def viewStadiums():
    stadiums = stadium_col.find()
    return render_template("viewStadiums.html",stadiums=stadiums)


@app.route("/addTimeSlots")
def addTimeSlots():
    stadiums = stadium_col.find()
    return render_template("addTimeSlots.html",stadiums=stadiums)


@app.route("/addTimeSlots1",methods=['post'])
def addTimeSlots1():
    stadium_id = ObjectId(request.form.get("stadium_id"))
    date = request.form.get("date")
    time = request.form.get("time")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    start_time = datetime.datetime(*[int(v) for v in start_time.replace('T', '-').replace(':', '-').split('-')])
    end_time = datetime.datetime(*[int(v) for v in end_time.replace('T', '-').replace(':', '-').split('-')])
    print(type(start_time))
    print(type(end_time))
    times_slots = time_slot_col.find({"stadium_id":ObjectId(stadium_id),"status":'Available'})
    for times_slot in times_slots:
        old_from_time = times_slot['start_time']
        old_to_time = times_slot['end_time']
        print(type(old_to_time))
        print(type(old_from_time))
        if (old_from_time >= start_time and old_from_time <= end_time) and (old_to_time >= start_time and old_to_time >= end_time):
            return render_template("message.html", msg='Time Conflict occurred for  Stadium. fails to Add Time Slots',color='text-danger')
        elif (old_from_time <= start_time and old_from_time <= end_time) and (old_to_time >= start_time and old_to_time <= end_time):
            return render_template("message.html", msg='Time Conflict occurred for  Stadium. fails to Add Time Slots',color='text-danger')
        elif (old_from_time <= start_time and old_from_time <= end_time) and (old_to_time >= start_time and old_to_time >= end_time):
            return render_template("message.html", msg='Time Conflict occurred for  Stadium. fails to Add Time Slots',color='text-danger')
        elif (old_from_time >= start_time and old_from_time <= end_time) and (old_to_time >= start_time and old_to_time <= end_time):
            return render_template("message.html", msg='Time Conflict occurred for  Stadium. fails to Add Time Slots',color='text-danger')
    time_slot_col.insert_one({"date":str(datetime.date.today()),"start_time":(start_time),"end_time":(end_time),"stadium_id":ObjectId(stadium_id),"status":'Available'})
    return render_template("message.html",msg='Time Slots Added For Stadium',color='text-success')


@app.route("/viewTimeSlots")
def viewTimeSlots():
    today = datetime.datetime.now()
    query = {"start_time": {"$gte": today},"status":"Available"}
    time_slots = time_slot_col.find(query)
    time_slots = list(time_slots)
    return render_template("viewTimeSlots.html",time_slots=time_slots, get_stadiumId=get_stadiumId,isSlotBooked=isSlotBooked)

def get_stadiumId(stadium_id):
    stadium = stadium_col.find_one({"_id":ObjectId(stadium_id)})
    return stadium


@app.route("/audianLoginPage1",methods=['post'])
def audianLoginPage1():
    email = request.form.get("email")
    otp = random.randint(1000, 10000)
    query = {"email":email}
    total_count = audience_col.count_documents(query)
    send_email("Stadium Seat Booking", "Use This OTP, " + str(otp) + ", To login Your account", email)
    if total_count > 0:
        return render_template("login_to_home.html", otp=otp, email=email)
    else:
        return render_template("audianRegister.html", otp=otp, email=email)



@app.route("/audianRegister1", methods=['post'])
def audianRegister1():
    email = request.form.get('email')
    otp = request.form.get('otp')
    name = request.form.get("name")
    phone = request.form.get("phone")
    otp2 = request.form.get('otp2')
    if otp == otp2:
        audian_id = audience_col.insert_one({"name": name, "email": email, "phone": phone})
        session['audian_id'] = str(audian_id.inserted_id)
        session['role'] = 'audian'
        session['email'] = 'email'
        return render_template("audianHome.html")
    else:
        return render_template("message.html", msg='Invalid otp', color='bg-danger')




@app.route("/login_to_home1", methods=['post'])
def login_to_home1():
    email = request.form.get("email")
    myquery = {"email": email}
    audian = audience_col.find_one(myquery)
    otp = request.form.get("otp")
    otp2 = request.form.get("otp2")
    if otp == otp2:
        session['audian_id'] = str(audian['_id'])
        session['role'] = 'audian'
        session['email'] = 'email'
        return redirect("/audianHome")
    else:
        return render_template("message.html", msg='Invalid  Otp ', color='text-danger')


@app.route("/audianHome")
def audianHome():
    audian = audience_col.find_one({'_id':ObjectId(session['audian_id'])})
    return render_template("audianHome.html",audian=audian)


@app.route("/addGameSchedule",methods=['post'])
def addGameSchedule():
    time_slot_id = ObjectId(request.form.get("time_slot_id"))
    return render_template("addGameSchedule.html",time_slot_id=time_slot_id)


@app.route("/addGameSchedule1",methods=['post'])
def addGameSchedule1():
    game_title = request.form.get("game_title")
    no_of_teams = request.form.get("no_of_teams")
    no_of_players_in_team = request.form.get("no_of_players_in_team")
    time_slot_id = ObjectId(request.form.get("time_slot_id"))
    duration = request.form.get("duration")
    schedule_col.insert_one({"game_title": game_title,"no_of_teams": no_of_teams,"no_of_players_in_team":no_of_players_in_team,"duration":duration,"time_slot_id":ObjectId(time_slot_id),"gameOrganiser_id":ObjectId(session['gameOrganiser_id'])})

    time_slot_col.update_one({'_id':ObjectId(time_slot_id)},{"$set":{"status":'Slot Booked'}})
    return render_template("message.html",msg='Game Schedule Added',color='text-success')


@app.route("/viewGameSchedules")
def viewGameSchedules():
    query = {"gameOrganiser_id":ObjectId(session['gameOrganiser_id'])}
    game_schedules = schedule_col.find(query)
    game_schedules = list(game_schedules)
    game_schedules.reverse()
    if len(game_schedules) ==0:
        return render_template("message.html",msg='Schedules Not Found',color='text-warning')
    return render_template("viewGameSchedules.html",game_schedules=game_schedules,get_time_slots=get_time_slots,get_stadium_by_timeSlots=get_stadium_by_timeSlots)


def get_time_slots(time_slot_id):
    times_slot = time_slot_col.find_one({"_id":ObjectId(time_slot_id)})
    return times_slot

def get_stadium_by_timeSlots(stadium_id):
    stadium = stadium_col.find_one({"_id":ObjectId(stadium_id)})
    return stadium


def isSlotBooked(time_slot_id):
    query = {"time_slot_id":ObjectId(time_slot_id),"gameOrganiser_id":ObjectId(session['gameOrganiser_id'])}
    count = schedule_col.count_documents(query)
    if count == 0:
        return True
    else:
        return False


@app.route("/viewTimeSlot")
def viewTimeSlot():
    time_slots = time_slot_col.find()
    return render_template("viewTimeSlot.html",get_stadiumId=get_stadiumId,time_slots=time_slots)


@app.route("/addTickets")
def addTickets():
    schedule_id = ObjectId(request.args.get("schedule_id"))
    return render_template("addTickets.html",schedule_id=schedule_id)



@app.route("/addTickets1",methods=['post'])
def addTickets1():
    no_of_seats = request.form.get("no_of_seats")
    price_per_seat = request.form.get("price_per_seat")
    is_coupleSeat = request.form.get("is_coupleSeat")
    complimentary_food = request.form.get("complimentary_food")
    schedule_id = ObjectId(request.form.get("schedule_id"))
    ticket_col.insert_one({"no_of_seats":no_of_seats,"price_per_seat":price_per_seat,"is_coupleSeat":is_coupleSeat,"complimentary_food":complimentary_food,"schedule_id":ObjectId(schedule_id)})
    return render_template("message.html",msg='Ticket Added',color='text-primary')


@app.route("/viewTickets")
def viewTickets():
    schedule_id = ObjectId(request.args.get("schedule_id"))
    tickets = ticket_col.find({"schedule_id":ObjectId(schedule_id)})
    return render_template("viewTickets.html",tickets=tickets)


@app.route("/viewUpcomingSchedules")
def viewUpcomingSchedules():
    today = datetime.datetime.now()
    query = {"start_time": {"$gte": today}}
    time_slots = time_slot_col.find(query)
    time_slots = list(time_slots)
    if len(time_slots) == 0:
        return render_template("message.html",msg='Schedules Not Available',color='text-warning')
    time_slot_ids = []
    for time_slot in time_slots:
        time_slot_ids.append({"time_slot_id":time_slot['_id']})
    query = {"$or": time_slot_ids}
    game_schedules = schedule_col.find(query)
    game_schedules = list(game_schedules)
    if len(game_schedules) == 0:
        return render_template("message.html",msg='No Upcoming Schedules',color='text-warning')
    return render_template("viewUpcomingSchedules.html",game_schedules=game_schedules,get_time_slots=get_time_slots,get_stadium_by_timeSlots=get_stadium_by_timeSlots)


@app.route("/bookTickets",methods=['post'])
def bookTickets():
    schedule_id = ObjectId(request.form.get("schedule_id"))
    ticket_id = ObjectId(request.form.get("ticket_id"))
    ticket = ticket_col.find_one({"_id":ObjectId(ticket_id)})
    return render_template("bookTickets.html",ticket=ticket,str=str,isSeatBooked=isSeatBooked,schedule_id=schedule_id,ticket_id=ticket_id,int=int)


@app.route("/bookTickets1",methods=['post'])
def bookTickets1():
    schedule_id = ObjectId(request.form.get("schedule_id"))
    ticket_id = ObjectId(request.form.get("ticket_id"))
    schedules = schedule_col.find_one({"_id": ObjectId(schedule_id)})
    # movie_id = schedules['movie_id']
    # movie = movie_col.find_one({'_id': ObjectId(movie_id)})
    # print(movie)
    ticket = ticket_col.find_one({"_id": ObjectId(ticket_id)})
    seat_numbers = []
    totalPrice = 0
    for i in range(int(ticket['no_of_seats'])):
        seat = request.form.get(str(ticket['_id']) + "seat" + str(i))
        if seat == 'on':
            seatDetails = {"seat": str(i)}
            seat_numbers.append(seatDetails)
            totalPrice = totalPrice + int(ticket['price_per_seat'])
    seat_numbers = list(seat_numbers)
    if len(seat_numbers) > 10:
        return render_template("message.html",msg='One Person Can Book 10 Tickets Only',color='text-danger')
    query = {"schedule_id": ObjectId(schedule_id), "ticket_id": ticket_id, "booking_date": datetime.datetime.now(),"seat_numbers": seat_numbers, "totalPrice": totalPrice, "audian_id": ObjectId(session['audian_id']),"booking_status": 'Payment Pending'}
    result = booking_col.insert_one(query)
    booking_id = result.inserted_id
    return render_template("bookTickets1.html",booking_id=booking_id,get_timeSlot_by_scheduleTime_id=get_timeSlot_by_scheduleTime_id,totalPrice=totalPrice,seat_numbers=seat_numbers,schedules=schedules,get_stadium_by_scheduleTime_id=get_stadium_by_scheduleTime_id)


def get_stadium_by_scheduleTime_id(time_slot_id):
    time_slot = time_slot_col.find_one({"_id":ObjectId(time_slot_id)})
    stadium_id = time_slot['stadium_id']
    stadium = stadium_col.find_one({"_id":ObjectId(stadium_id)})
    return stadium

def get_timeSlot_by_scheduleTime_id(time_slot_id):
    time_slot = time_slot_col.find_one({"_id": ObjectId(time_slot_id)})
    return time_slot


@app.route("/pay_amount")
def pay_amount():
    booking_id = ObjectId(request.args.get("booking_id"))
    totalPrice = request.args.get("totalPrice")
    return render_template("pay_amount.html",totalPrice=totalPrice,booking_id=booking_id)


@app.route("/pay_amount1",methods=['post'])
def pay_amount1():
    booking_id = ObjectId(request.form.get("booking_id"))
    query = {"$set":{"booking_status":'Booking Confirmed'}}
    booking_col.update_one({"_id":ObjectId(booking_id)},query)
    return render_template("message.html",msg='Tickets Booked Successfully',color='text-success')

def isSeatBooked(seat,ticket_id):
    query = {"ticket_id":ObjectId(ticket_id)}
    bookings = booking_col.find(query)
    for booking in bookings:
        for ticket in booking['seat_numbers']:
            if (str(ticket['seat'])) == str(seat):
                return True
    return False

@app.route("/ViewBookings")
def ViewBookings():
    query = {}
    if session['role'] == 'gameOrganiser':
        ticket_id = request.args.get("ticket_id")
        query = {'ticket_id':ObjectId(ticket_id)}
    elif session['role'] == 'audian':
        query = {"audian_id":ObjectId(session['audian_id'])}
    bookings = booking_col.find(query)
    bookings = list(bookings)
    if len(bookings) == 0:
        return render_template("message.html",msg='Bookings Not Available')
    return render_template("ViewBookings.html",get_audian_by_booking=get_audian_by_booking,bookings=bookings,get_schedule_by_booking=get_schedule_by_booking,get_tickets_by_booking=get_tickets_by_booking,get_stadium_by_scheduleTime_id=get_stadium_by_scheduleTime_id,get_timeSlot_by_scheduleTime_id=get_timeSlot_by_scheduleTime_id)


def get_audian_by_booking(audian_id):
    audian = audience_col.find_one({"_id":ObjectId(audian_id)})
    return audian

def get_schedule_by_booking(schedule_id):
    schedule = schedule_col.find_one({'_id':ObjectId(schedule_id)})
    return schedule

def get_tickets_by_booking(ticket_id):
    ticket = ticket_col.find_one({'_id':ObjectId(ticket_id)})
    return ticket


@app.route("/cancel_booking",methods=['post'])
def cancel_booking():
    booking_id = request.form.get("booking_id")
    query = {"$set":{"booking_status":'Booking Cancelled'}}
    booking_col.update_one({'_id':ObjectId(booking_id)},query)
    return ViewBookings()


@app.route("/transferTickets",methods=['post'])
def transferTickets():
    booking_id = ObjectId(request.form.get("booking_id"))
    return render_template("transferTickets.html",booking_id=booking_id)


@app.route("/transferTickets1",methods=['post'])
def transferTickets1():
    email = request.form.get("email")
    booking_id = ObjectId(request.form.get("booking_id"))
    query = {'email':email}
    count = audience_col.count_documents(query)
    if count == 0:
        return render_template("message.html",msg='Audian Not Found',color='text-danger')
    else:
        audian = audience_col.find_one(query)
        audian_id = audian['_id']
        query1 = {"$set":{"audian_id":ObjectId(audian_id)}}
        booking_col.update_one({"_id":ObjectId(booking_id)},query1)
        return render_template("message.html", msg='Tickets Transferred', color='text-success')


@app.route("/updateStadium")
def updateStadium():
    stadium_id = request.args.get("stadium_id")
    stadium = stadium_col.find_one({"_id": ObjectId(stadium_id)})
    return render_template("updateStadium.html",stadium=stadium,stadium_id=stadium_id)

@app.route("/updateStadium1",methods=['post'])
def updateStadium1():
    stadium_id = request.form.get("stadium_id")
    stadium_name = request.form.get("stadium_name")
    location = request.form.get("location")
    address = request.form.get("address")
    query = {"$set":{"stadium_name":stadium_name,"location":location,"address":address}}
    stadium_col.update_one({"_id":ObjectId(stadium_id)},query)
    return redirect("/viewStadiums")

# app.run(debug=True)

app.run(host='0.0.0.0', port=20470,debug=True)