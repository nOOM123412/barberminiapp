from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, Booking, SupportMessage

app = FastAPI()

# Разрешаем запросы с любого сайта (чтобы GitHub Pages мог стучаться)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель данных для приема бронирования
class BookingCreate(BaseModel):
    user_id: int
    user_name: str
    username: str | None = None
    service_id: str
    master_id: str
    date: str
    time: str

# Модель данных для поддержки
class SupportCreate(BaseModel):
    user_id: int
    user_name: str
    message: str

# 1. Эндпоинт для получения занятых слотов (Mini App будет вызывать его при открытии)
@app.get("/api/booked_slots")
def get_booked_slots(db: Session = Depends(get_db)):
    # Достаем все записи из БД
    bookings = db.query(Booking).all()
    # Возвращаем их в виде списка JSON
    return [{"master_id": b.master_id, "date": b.date, "time": b.time} for b in bookings]

# 2. Эндпоинт для создания новой записи
@app.post("/api/book")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    # Проверяем, не занято ли уже это время
    existing = db.query(Booking).filter(
        Booking.master_id == booking.master_id,
        Booking.date == booking.date,
        Booking.time == booking.time
    ).first()
    
    if existing:
        return {"status": "error", "message": "Это время уже занято"}

    new_booking = Booking(
        user_id=booking.user_id,
        user_name=booking.user_name,
        username=booking.username,
        service_id=booking.service_id,
        master_id=booking.master_id,
        date=booking.date,
        time=booking.time
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return {"status": "ok", "booking_id": new_booking.id}

# 3. Эндпоинт для поддержки
@app.post("/api/support")
def create_support(msg: SupportCreate, db: Session = Depends(get_db)):
    new_msg = SupportMessage(
        user_id=msg.user_id,
        user_name=msg.user_name,
        message=msg.message
    )
    db.add(new_msg)
    db.commit()
    return {"status": "ok"}

# 4. Эндпоинт для получения записей конкретного пользователя (для вкладки "Мои записи")
@app.get("/api/my_bookings/{user_id}")
def get_my_bookings(user_id: int, db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return bookings
