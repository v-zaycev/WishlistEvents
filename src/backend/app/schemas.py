from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date

# ========== User schemas ==========
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str
    password: str = Field(..., min_length=6, max_length=127)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    user_id: int
    name: str
    email: str
    message: str = "Login successful"

# ========== Wishlist schemas ==========
class WishlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class WishlistResponse(BaseModel):
    id: int
    name: str
    user_id: int

    class Config:
        from_attributes = True

class WishlistWithItemsResponse(BaseModel):
    id: int
    name: str
    user_id: int
    items: List['ItemResponse'] = []

    class Config:
        from_attributes = True

# ========== Item schemas ==========
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Optional[float] = Field(None, ge=0, description="Цена (опционально)")
    link: Optional[str] = Field(None, max_length=500, description="Ссылка на товар")
    description: Optional[str] = Field(None, description="Описание")

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, ge=0)
    link: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    price: Optional[float] = None
    link: Optional[str] = None
    description: Optional[str] = None
    status: str
    wishlist_id: int
    booked_by: Optional[int] = None
    booked_event_id: Optional[int] = None

    class Config:
        from_attributes = True

# ========== Event schemas ==========
class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    date: date

class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    date: date
    organizer_id: int

    class Config:
        from_attributes = True

class EventParticipantResponse(BaseModel):
    user_id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class EventWishlistResponse(BaseModel):
    wishlist_id: int
    wishlist_name: str
    items_count: int

    class Config:
        from_attributes = True

class EventDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    date: date
    organizer_id: int
    organizer_name: str
    participants: List[EventParticipantResponse] = []
    wishlists: List[EventWishlistResponse] = []

    class Config:
        from_attributes = True

class EventWishlistCreate(BaseModel):
    wishlist_id: int

# ========== Expense schemas ==========
class ExpenseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    total_amount: float = Field(..., gt=0)

class ExpenseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    total_amount: float
    event_id: int
    paid_by: Optional[int] = None

    class Config:
        from_attributes = True

# ========== Booking schemas ==========
class EventItemResponse(BaseModel):
    id: int
    name: str
    price: Optional[float] = None
    link: Optional[str] = None
    description: Optional[str] = None
    wishlist_id: int
    wishlist_name: str
    is_booked: bool
    booked_by_user_id: Optional[int] = None
    booked_by_user_name: Optional[str] = None

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    message: str
    item_id: int
    user_id: int
    event_id: int
    item_name: str

WishlistWithItemsResponse.model_rebuild()
