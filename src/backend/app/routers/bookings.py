from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db
from app.auth import get_user_by_id

router = APIRouter(prefix="/events", tags=["bookings"])

def get_event_or_404(db: Session, event_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event

def check_event_access(db: Session, event_id: int, user_id: int):
    event = get_event_or_404(db, event_id)

    if event.organizer_id == user_id:
        return event

    participant = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.user_id == user_id
    ).first()

    if participant:
        return event

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have access to this event"
    )

def get_item_from_event_wishlists(db: Session, event_id: int, item_id: int):
    event_wishlists = db.query(models.EventWishlist).filter(
        models.EventWishlist.event_id == event_id
    ).all()

    wishlist_ids = [ew.wishlist_id for ew in event_wishlists]

    if not wishlist_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No wishlists attached to this event"
        )

    item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.wishlist_id.in_(wishlist_ids)
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in event wishlists"
        )

    return item

# ========== Эндпоинты для бронирования ==========

# Получить все позиции из вишлистов, привязанных к событию (с флагом бронирования)
@router.get("/{event_id}/items", response_model=List[schemas.EventItemResponse])
def get_event_items(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = check_event_access(db, event_id, user_id)

    event_wishlists = db.query(models.EventWishlist).filter(
        models.EventWishlist.event_id == event_id
    ).all()

    if not event_wishlists:
        return []

    wishlist_ids = [ew.wishlist_id for ew in event_wishlists]

    items = db.query(models.Item).filter(
        models.Item.wishlist_id.in_(wishlist_ids)
    ).all()

    wishlists = db.query(models.Wishlist).filter(
        models.Wishlist.id.in_(wishlist_ids)
    ).all()
    wishlist_dict = {w.id: w.name for w in wishlists}

    result = []
    for item in items:
        booked_by_name = None
        if item.booked_by:
            booked_user = get_user_by_id(db, item.booked_by)
            booked_by_name = booked_user.name if booked_user else None

        result.append(schemas.EventItemResponse(
            id=item.id,
            name=item.name,
            price=float(item.price) if item.price else None,
            link=item.link,
            description=item.description,
            wishlist_id=item.wishlist_id,
            wishlist_name=wishlist_dict.get(item.wishlist_id, "Unknown"),
            is_booked=item.booked_by is not None,
            booked_by_user_id=item.booked_by,
            booked_by_user_name=booked_by_name
        ))

    return result

# Забронировать подарок на событии
@router.post("/{event_id}/items/{item_id}/book", response_model=schemas.BookingResponse)
def book_item(
    event_id: int,
    item_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = check_event_access(db, event_id, user_id)

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    item = get_item_from_event_wishlists(db, event_id, item_id)

    if item.booked_by is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item already booked by user ID {item.booked_by}"
        )

    item.booked_by = user_id
    item.booked_event_id = event_id
    item.status = "booked"

    db.commit()
    db.refresh(item)

    return schemas.BookingResponse(
        message="Item booked successfully",
        item_id=item.id,
        user_id=user_id,
        event_id=event_id,
        item_name=item.name
    )

# Отменить бронирование подарка
@router.delete("/{event_id}/items/{item_id}/book", response_model=schemas.BookingResponse)
def unbook_item(
    event_id: int,
    item_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = check_event_access(db, event_id, user_id)

    item = get_item_from_event_wishlists(db, event_id, item_id)

    if item.booked_by is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is not booked"
        )

    if item.booked_by != user_id and event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unbook your own bookings"
        )

    old_booked_by = item.booked_by
    item.booked_by = None
    item.booked_event_id = None
    item.status = "active"

    db.commit()
    db.refresh(item)

    return schemas.BookingResponse(
        message="Booking cancelled successfully",
        item_id=item.id,
        user_id=old_booked_by,
        event_id=event_id,
        item_name=item.name
    )
