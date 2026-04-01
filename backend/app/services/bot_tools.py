import uuid
import re
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from sqlalchemy import select, func
from langchain_core.tools import tool
from app.database import AsyncSessionLocal
from app.models.clinic_rule import ClinicRule
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.blocked_slot import BlockedSlot
from app.core.config import settings
import razorpay
import redis.asyncio as redis

# Initialize Redis for Slot Locking
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Initialize Razorpay Client
razor_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razor_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@tool
async def get_doctors() -> str:
    """
    Retrieves a list of all available doctors in the clinic.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Doctor).where(Doctor.is_active == True))
        docs = result.scalars().all()
        if not docs:
            return "No doctors are currently available."
        return "Available Doctors:\n" + "\n".join([f"- Dr. {d.name} ({d.specialization}, Fee: ₹{d.consultation_fee})" for d in docs])


@tool
async def get_doctor_details(doctor_name: str) -> str:
    """
    Fetches detailed information about a specific doctor.
    Supports fuzzy matching. If multiple matches, returns a list.
    """
    search_name = doctor_name.replace("Dr. ", "").replace("Dr.", "").strip()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.name.ilike(f"%{search_name}%"), Doctor.is_active == True)
        )
        doctors = result.scalars().all()
        
        if not doctors:
            return f"Could not find any doctor matching '{doctor_name}'."
        
        if len(doctors) > 1:
            listing = [f"- Dr. {d.name} ({d.specialization})" for d in doctors]
            return "Multiple doctors found. Please specify:\n" + "\n".join(listing)
        
        doctor = doctors[0]
        info = [
            f"Full Name: Dr. {doctor.name}",
            f"Specialization: {doctor.specialization or 'General Practice'}",
            f"Degree: {doctor.degree or 'N/A'}",
            f"Consultation Fee: ₹{doctor.consultation_fee}",
            f"Bio: {doctor.bio or 'Experienced professional at MediCall.'}"
        ]
        return "\n".join(info)


@tool
async def get_patient_history(phone: str) -> str:
    """
    Fetches patient details and their past 3 appointments by phone number.
    Returns "New Patient" if not found.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Patient).where(Patient.phone == phone)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            return "Status: New Patient (Not registered). Please ask for their full name and reason for visit to register them."
        
        # Fetch appts
        appt_result = await session.execute(
            select(Appointment, Doctor)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .where(Appointment.patient_id == patient.id)
            .order_by(Appointment.appointment_date.desc())
            .limit(3)
        )
        history = appt_result.all()
        
        details = [
            f"Status: Registered Patient",
            f"Patient ID: {patient.id}",
            f"Name: {patient.name}",
            f"DOB: {patient.dob or 'N/A'}",
            f"Gender: {patient.gender or 'N/A'}",
            f"Registration Date: {patient.created_at.date()}",
            "\nPast Appointments:"
        ]
        
        if not history:
            details.append("- No past appointments found yet.")
        else:
            for appt, doc in history:
                details.append(f"- {appt.appointment_date} with Dr. {doc.name} (Status: {appt.status.value})")
            
        return "\n".join(details)


@tool
async def get_clinic_info() -> str:
    """
    Provides general information about the clinic (location, hours, services offered).
    """
    info = [
        "🏥 MediCall Multi-Specialty Clinic",
        "📍 Location: Sector 5, HSR Layout, Bangalore - 560102",
        "⏰ Hours: Mon-Sat, 09:00 AM - 08:30 PM (Sundays on call only)",
        "📞 Emergency: +91 99999-00001",
        "\n✅ Services Offered:",
        "- General Consultation & Fever Clinic",
        "- Pediatrics (Child Specialist)",
        "- Cardiology & Orthopedics",
        "- Dental & Eye Checkups",
        "- Laboratory & Pharmacy (Home delivery available)",
        "\nNote: We accept all major UPI and health insurance."
    ]
    return "\n".join(info)


@tool
async def check_available_slots(doctor_name: str, date_str: str) -> str:
    """
    Checks available 30-minute slots for a doctor on a specific date.
    Returns a numbered list for easy selection.
    """
    cleaned_name = doctor_name.replace("Dr.", "").replace("dr.", "").strip()
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Doctor).where(Doctor.name.ilike(f"%{cleaned_name}%")))
        doctor = result.scalar_one_or_none()
        if not doctor: return f"Doctor '{doctor_name}' not found."

        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError: return "Invalid date format. Use YYYY-MM-DD."

        # Booked Slots
        appt_result = await db.execute(
            select(Appointment.slot_time).where(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == query_date,
                Appointment.status != AppointmentStatus.cancelled
            )
        )
        booked_slots = {r[0].strftime("%I:%M %p") for r in appt_result.all() if r[0]}

        # Blocked Slots
        blocked_result = await db.execute(
            select(BlockedSlot.slot_time).where(
                BlockedSlot.doctor_id == doctor.id,
                BlockedSlot.date == query_date
            )
        )
        blocked_slots = {r[0].strftime("%I:%M %p") for r in blocked_result.all() if r[0]}

        # Schedule
        schedule = doctor.schedule or {}
        day_name = query_date.strftime("%a").lower()
        if schedule and not schedule.get(day_name, True):
            return f"Dr. {doctor.name} does not consult on {query_date.strftime('%A')}s."

        start_str = schedule.get("start", "09:00")
        end_str = schedule.get("end", "20:00")
        duration = schedule.get("slot_duration_mins", 30)

        available = []
        try:
            curr = datetime.combine(query_date, datetime.strptime(start_str, "%H:%M").time())
            end_time = datetime.combine(query_date, datetime.strptime(end_str, "%H:%M").time())
            
            has_explicit_break = "break_start" in schedule
            break_start_time = time(13, 0)
            break_end_time = time(16, 0)
            if has_explicit_break:
                break_start_time = datetime.strptime(schedule["break_start"], "%H:%M").time()
                break_end_time = datetime.strptime(schedule["break_end"], "%H:%M").time()

            while curr < end_time:
                if break_start_time <= curr.time() < break_end_time:
                    curr += timedelta(minutes=duration)
                    continue

                slot_str = curr.strftime("%I:%M %p")
                if slot_str not in booked_slots and slot_str not in blocked_slots:
                    available.append(slot_str)
                curr += timedelta(minutes=duration)
        except Exception as e:
            return f"Error: {str(e)}"

        if not available: return f"No slots available for Dr. {doctor.name} on {date_str}."
        
        resp = f"Available slots for Dr. {doctor.name} on {date_str}:\n"
        for i, s in enumerate(available[:12], 1):
            resp += f"{i}. {s}\n"
        resp += "\nReply with the number (e.g. '1') to book."
        return resp


@tool
async def book_appointment(
    doctor_name: str, 
    date_str: str, 
    time_str: str, 
    patient_phone: str, 
    is_first_time: str, 
    patient_name: str, 
    reason: str = "WhatsApp Booking"
) -> str:
    """
    Books an appointment. 
    - time_str: Can be a time (e.g. '10:00 AM') or a list number (e.g. '1').
    - is_first_time: "true" if the patient has never visited before, else "false".
    - patient_name: MUST be the patient's full name. Do not use placeholders like "Unknown".
    """
    cleaned_name = doctor_name.replace("Dr.", "").replace("dr.", "").strip()
    
    # Normalize boolean
    is_first_time_bool = str(is_first_time).lower() == "true"
    
    # Reject placeholders
    if patient_name.lower() in ["unknown", "n/a", "none", ""]:
        return "Error: I need the patient's full name to complete the booking. Please ask them for it."

    async with AsyncSessionLocal() as db:
        doc_result = await db.execute(select(Doctor).where(Doctor.name.ilike(f"%{cleaned_name}%")))
        doctor = doc_result.scalar_one_or_none()
        if not doctor: return f"Doctor '{doctor_name}' not found."

        try:
            appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError: return "Invalid date format."

        # Resolve numeric selection
        final_time_str = time_str
        if time_str.strip().isdigit():
            # Correctly handle number-only replies
            slots_info = await check_available_slots.ainvoke({"doctor_name": doctor_name, "date_str": date_str})
            # Handle cases where hour might be single digit (e.g. 9:00 AM)
            matches = re.findall(r"\d+\.\s+(\d{1,2}:\d{2}\s+[APM]{2})", slots_info)
            idx = int(time_str.strip()) - 1
            if 0 <= idx < len(matches):
                final_time_str = matches[idx]
            else:
                return f"Selection '{time_str}' is invalid for the available list."

        # Flexible time parsing
        appt_time = None
        for fmt in ("%I:%M %p", "%I %p", "%H:%M", "%H"):
            try:
                appt_time = datetime.strptime(final_time_str.strip(), fmt).time()
                break
            except ValueError:
                continue
        
        if not appt_time:
            return f"Invalid time format: {final_time_str}. Please use 'HH:MM AM/PM'."

        # 3. Concurrency Control: Redis Lock to prevent double-booking
        lock_key = f"lock:doctor:{doctor.id}:date:{appt_date}:time:{appt_time}"
        try:
            async with redis_client.lock(lock_key, timeout=10):
                # Double-check availability inside the lock
                check_res = await db.execute(
                    select(Appointment).where(
                        Appointment.doctor_id == doctor.id,
                        Appointment.appointment_date == appt_date,
                        Appointment.slot_time == appt_time,
                        Appointment.status != AppointmentStatus.cancelled
                    )
                )
                if check_res.scalars().first():
                    return f"Apologies, but Dr. {doctor.name} was just booked for {final_time_str} by another patient. Please choose a different slot."

                # Patient lookup/creation
                p_res = await db.execute(select(Patient).where(Patient.phone == patient_phone))
                patient = p_res.scalar_one_or_none()
                if not patient:
                    patient = Patient(id=str(uuid.uuid4()), clinic_id=doctor.clinic_id, name=patient_name, phone=patient_phone)
                    db.add(patient)
                    await db.flush()

                # Create appointment with pending_payment status
                appt = Appointment(
                    id=str(uuid.uuid4()), 
                    clinic_id=doctor.clinic_id, 
                    patient_id=patient.id, 
                    doctor_id=doctor.id, 
                    appointment_date=appt_date, 
                    slot_time=appt_time, 
                    token_number=None, # Token assigned AFTER payment
                    status=AppointmentStatus.pending_payment, 
                    reason=reason
                )
                db.add(appt)
                await db.commit()
                return (
                    f"Slot for Dr. {doctor.name} on {appt_date} at {final_time_str} is now RESERVED for you. "
                    "To finalize the booking and get your Token Number, please complete the payment using the link I'll provide next."
                )
        except Exception as e:
            return f"Error during booking: {str(e)}"

@tool
async def cancel_appointment(appointment_id: Optional[str] = None) -> str:
    """
    Cancels an appointment. This is a high-priority action that triggers waitlist notifications.
    """
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(Appointment).where(Appointment.status != AppointmentStatus.cancelled)
            # Find latest if no ID
            if not appointment_id:
                stmt = stmt.order_by(Appointment.created_at.desc())
            else:
                stmt = stmt.where(Appointment.id == appointment_id)
            
            result = await db.execute(stmt)
            appt = result.scalars().first()
            if not appt: return "No active appointment found to cancel."
            
            doctor_name = appt.doctor.name
            date_str = appt.appointment_date.strftime("%Y-%m-%d")
            time_str = appt.slot_time.strftime("%I:%M %p")
            
            appt.status = AppointmentStatus.cancelled
            await db.commit()
            
            # Trigger Waitlist Notification
            await notify_next_on_waitlist(appt.doctor_id, appt.appointment_date, appt.slot_time)
            
            return f"Appointment for Dr. {doctor_name} on {date_str} at {time_str} has been CANCELLED. The slot is now available, and I've notified the waitlist."
    except Exception as e:
        return f"Error cancelling: {str(e)}"


@tool
async def add_to_waitlist(doctor_name: str, date_str: str, patient_phone: str) -> str:
    """
    Adds a patient to the automated waitlist for a specific doctor and date.
    Use this when all slots are full.
    """
    try:
        from app.models.waitlist import Waitlist, WaitlistStatus
        async with AsyncSessionLocal() as db:
            doc_res = await db.execute(select(Doctor).where(Doctor.name.ilike(f"%{doctor_name}%")))
            doctor = doc_res.scalar_one_or_none()
            if not doctor: return f"Doctor {doctor_name} not found."
            
            p_res = await db.execute(select(Patient).where(Patient.phone == patient_phone))
            patient = p_res.scalar_one_or_none()
            if not patient: return "Please register your name first before joining the waitlist."
            
            wait_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            entry = Waitlist(
                id=str(uuid.uuid4()),
                patient_id=patient.id,
                doctor_id=doctor.id,
                preferred_date=wait_date,
                status=WaitlistStatus.waiting
            )
            db.add(entry)
            await db.commit()
            return f"Success! You've been added to the Waitlist for Dr. {doctor.name} on {date_str}. I will WhatsApp you the moment a slot opens up!"
    except Exception as e:
        return f"Error adding to waitlist: {str(e)}"


async def notify_next_on_waitlist(doctor_id: str, appt_date: date, appt_time: time):
    """Internal helper to notify the first waiting patient."""
    from app.models.waitlist import Waitlist, WaitlistStatus
    async with AsyncSessionLocal() as db:
        stmt = (
            select(Waitlist)
            .where(Waitlist.doctor_id == doctor_id, Waitlist.preferred_date == appt_date, Waitlist.status == WaitlistStatus.waiting)
            .order_by(Waitlist.created_at.asc())
        )
        res = await db.execute(stmt)
        entry = res.scalars().first()
        if not entry: return
        
        # Update status
        entry.status = WaitlistStatus.notified
        await db.commit()
        
        # Send WhatsApp (Mocking the Twilio call for now)
        msg = (
            f"🔔 GOOD NEWS! A slot just opened up for Dr. {entry.doctor.name} on {appt_date} at {appt_time.strftime('%I:%M %p')}. "
            "Reply '1' to CLAIM this slot and book it now!"
        )
        print(f"WAITLIST NOTIFICATION to {entry.patient.phone}: {msg}")
        # send_whatsapp(entry.patient.phone, msg)

@tool
async def confirm_payment(appointment_id: Optional[str] = None) -> str:
    """
    Finalizes an appointment once payment is confirmed. 
    Call this when the patient says 'I have paid' or provides a txn ID.
    If appointment_id is not provided, it will look for the most recent pending session.
    """
    try:
        async with AsyncSessionLocal() as db:
            # If no ID, find latest pending for this phone (needs phone context usually)
            stmt = select(Appointment).where(Appointment.status == AppointmentStatus.pending_payment).order_by(Appointment.created_at.desc())
            result = await db.execute(stmt)
            appt = result.scalars().first()
            
            if not appt:
                return "No pending appointments found to confirm."
            
            # Update status to scheduled
            appt.status = AppointmentStatus.scheduled
            
            # Generate Token Number only now
            token_res = await db.execute(
                select(func.max(Appointment.token_number))
                .where(Appointment.doctor_id == appt.doctor_id, Appointment.appointment_date == appt.appointment_date)
            )
            token = (token_res.scalar() or 0) + 1
            appt.token_number = token
            
            await db.commit()
            return f"Payment Confirmed! 🎉 Your appointment is now officially BOOKED. Your Token Number is #{token}."
    except Exception as e:
        return f"Error confirming payment: {str(e)}"



@tool
async def reschedule_appointment(doctor_name: str, date_str: str, time_str: str, patient_phone: str) -> str:
    """
    Reschedules the latest scheduled appointment.
    """
    cleaned_name = doctor_name.replace("Dr.", "").replace("dr.", "").strip()
    async with AsyncSessionLocal() as db:
        doc_res = await db.execute(select(Doctor).where(Doctor.name.ilike(f"%{cleaned_name}%")))
        doctor = doc_res.scalar_one_or_none()
        if not doctor: return "Doctor not found."

        p_res = await db.execute(select(Patient).where(Patient.phone == patient_phone))
        patient = p_res.scalar_one_or_none()
        if not patient: return "Patient not found."

        appt_res = await db.execute(select(Appointment).where(Appointment.patient_id == patient.id, Appointment.status == AppointmentStatus.scheduled).order_by(Appointment.appointment_date.desc()))
        appt = appt_res.scalars().first()
        if not appt: return "No appointment found to reschedule."

        # Resolve numeric selection
        final_time_str = time_str
        if time_str.strip().isdigit():
            slots_info = await check_available_slots.ainvoke({"doctor_name": doctor_name, "date_str": date_str})
            matches = re.findall(r"\d+\.\s+(\d{2}:\d{2}\s+[APM]{2})", slots_info)
            idx = int(time_str.strip()) - 1
            if 0 <= idx < len(matches):
                final_time_str = matches[idx]

        try:
            appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            appt_time = datetime.strptime(final_time_str.strip(), "%I:%M %p").time()
        except ValueError: 
            return "Invalid date or time format provided."

        # 3. Concurrency Control: Redis Lock for the NEW slot
        lock_key = f"lock:doctor:{doctor.id}:date:{appt_date}:time:{appt_time}"
        try:
            async with redis_client.lock(lock_key, timeout=10):
                # Double-check if the target slot is free (excluding current appointment)
                check_res = await db.execute(
                    select(Appointment).where(
                        Appointment.doctor_id == doctor.id,
                        Appointment.appointment_date == appt_date,
                        Appointment.slot_time == appt_time,
                        Appointment.status != AppointmentStatus.cancelled,
                        Appointment.id != appt.id 
                    )
                )
                if check_res.scalars().first():
                    return f"Sorry, Dr. {doctor.name} is already booked for {final_time_str}. Please try another slot."

                appt.appointment_date = appt_date
                appt.slot_time = appt_time
                await db.commit()
                return f"Successfully rescheduled to {date_str} at {final_time_str}."
        
        except redis.exceptions.LockError:
            return "The system is currently busy. Please try rescheduling in a few seconds."


@tool
async def get_clinic_rules() -> str:
    """
    Fetches clinic rules and guidelines.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ClinicRule).where(ClinicRule.is_active == True))
        rules = result.scalars().all()
        if not rules: return "General rules apply."
        return "\n".join([f"- {r.rule_text}" for r in rules])


@tool
async def get_queue_status(phone: str) -> str:
    """
    Checks the real-time queue status for the patient's appointment today.
    Returns their position and the number of people ahead of them.
    """
    today = date.today()
    async with AsyncSessionLocal() as session:
        # 1. Find the patient
        patient_res = await session.execute(select(Patient).where(Patient.phone == phone))
        patient = patient_res.scalar_one_or_none()
        if not patient: 
            return "I couldn't find your records. Are you a new patient?"
        
        # 2. Find today's active appointment
        appt_res = await session.execute(
            select(Appointment)
            .where(
                Appointment.patient_id == patient.id,
                Appointment.appointment_date == today,
                Appointment.status.notin_([AppointmentStatus.cancelled, AppointmentStatus.no_show, AppointmentStatus.done])
            )
            .order_by(Appointment.token_number.asc())
        )
        appt = appt_res.scalars().first()
        if not appt: 
            return "You don't have any active appointments scheduled for today."
        
        # 3. Count people ahead (same doctor, lower token, not done)
        ahead_res = await session.execute(
            select(func.count(Appointment.id))
            .where(
                Appointment.doctor_id == appt.doctor_id,
                Appointment.appointment_date == today,
                Appointment.token_number < appt.token_number,
                Appointment.status.notin_([AppointmentStatus.done, AppointmentStatus.cancelled])
            )
        )
        people_ahead = ahead_res.scalar() or 0
        
        # 4. Get doctor name
        doc_res = await session.execute(select(Doctor).where(Doctor.id == appt.doctor_id))
        doctor = doc_res.scalar_one_or_none()
        
        status_msg = f"📍 Queue Status for Today:\n"
        status_msg += f"- Token: #{appt.token_number}\n"
        status_msg += f"- Doctor: Dr. {doctor.name if doctor else 'N/A'}\n"
        status_msg += f"- Current Status: {appt.status.value.replace('_', ' ').title()}\n"
        status_msg += f"- People ahead of you: {people_ahead}\n"
        
        if appt.status == AppointmentStatus.scheduled:
            status_msg += "\nPlease arrive at least 10 minutes before your slot."
        elif appt.status == AppointmentStatus.arrived:
            status_msg += "\nYou are in the active lobby. We will call you shortly!"
            
        return status_msg


@tool
async def get_payment_link(phone: str) -> str:
    """
    Generates an official Razorpay payment link for the patient's upcoming scheduled appointment.
    """
    async with AsyncSessionLocal() as session:
        # 1. Find the patient
        patient_res = await session.execute(select(Patient).where(Patient.phone == phone))
        patient = patient_res.scalar_one_or_none()
        if not patient: return "Patient not found."
        
        # 2. Find the next scheduled appointment
        appt_res = await session.execute(
            select(Appointment, Doctor)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .where(
                Appointment.patient_id == patient.id,
                Appointment.status == AppointmentStatus.scheduled
            )
            .order_by(Appointment.appointment_date.asc())
        )
        data = appt_res.first()
        if not data: 
            return "You don't have any upcoming scheduled appointments that require payment."
        
        appt, doctor = data
        amount_in_paise = int(doctor.consultation_fee * 100) # Razorpay works in paise
        
        # 3. Create Razorpay Payment Link
        if not razor_client:
            return (
                f"💳 Payment Request (Simulation Mode)\n"
                f"Doctor: Dr. {doctor.name}\n"
                f"Fee: ₹{doctor.consultation_fee}\n"
                f"Link: https://rzp.io/i/medicall_{appt.id[:8]}\n"
                f"(Note: Razorpay API keys are not configured yet. Please update .env)"
            )

        try:
            # Using the Razorpay v1/payment_links API
            link_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": f"Consultation with Dr. {doctor.name} at MediCall",
                "customer": {
                    "name": patient.name,
                    "contact": patient.phone
                },
                "notify": {
                    "sms": True,
                    "whatsapp": True
                },
                "reminder_enable": True,
                "notes": {
                    "appointment_id": appt.id,
                    "patient_id": patient.id
                },
                # In a real app, this would be a dynamic frontend URL
                "callback_url": f"https://medicall.app/payment-success?id={appt.id}",
                "callback_method": "get"
            }
            
            response = razor_client.payment_link.create(data=link_data)
            short_url = response.get("short_url")
            
            return (
                f"💳 Official Payment Request\n\n"
                f"Doctor: Dr. {doctor.name}\n"
                f"Fee: ₹{doctor.consultation_fee}\n"
                f"Appointment: {appt.appointment_date}\n\n"
                f"Please pay here: {short_url}\n\n"
                f"You will receive a confirmation message once the payment is successful."
            )
        except Exception as e:
            return f"Error generating Razorpay link: {str(e)}. Please try again later or pay at the clinic."


@tool
async def get_specialists_by_category(category: str) -> str:
    """
    Finds doctors based on their medical specialization category (e.g., 'Pediatrician', 'Cardiologist').
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Doctor).where(Doctor.specialization.ilike(f"%{category}%"), Doctor.is_active == True)
        )
        doctors = result.scalars().all()
        if not doctors:
            return f"No specialists found in the '{category}' category at this clinic."
        
        listing = [f"- Dr. {d.name} ({d.specialization}, Fee: ₹{d.consultation_fee})" for d in doctors]
        return f"Specialists in {category}:\n" + "\n".join(listing)


@tool
async def get_triage_recommendation(symptoms: str) -> str:
    """
    Analyzes symptoms and recommends the correct type of specialist to see.
    """
    # Simple rule-based triage for now, can be enhanced with an LLM call if needed.
    symptoms_lower = symptoms.lower()
    
    mapping = {
        "fever": "General Physician",
        "cough": "General Physician",
        "heart": "Cardiologist",
        "chest pain": "Cardiologist",
        "skin": "Dermatologist",
        "rash": "Dermatologist",
        "child": "Pediatrician",
        "baby": "Pediatrician",
        "kid": "Pediatrician",
        "bone": "Orthopedic",
        "fracture": "Orthopedic",
        "tooth": "Dentist",
        "teeth": "Dentist",
        "eye": "Ophthalmologist",
        "vision": "Ophthalmologist",
    }
    
    for key, spec in mapping.items():
        if key in symptoms_lower:
            return f"Based on your symptoms ('{symptoms}'), I recommend seeing a {spec}. Shall I find one for you?"
            
    return "I'm not exactly sure which specialist is best for those symptoms. I'd recommend starting with a General Physician for a primary checkup."

