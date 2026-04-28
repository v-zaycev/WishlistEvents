from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db
from app.auth import get_user_by_id

router = APIRouter(prefix="/events", tags=["events"])

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

def get_wishlist_or_404(db: Session, wishlist_id: int, user_id: int):
    wishlist = db.query(models.Wishlist).filter(
        models.Wishlist.id == wishlist_id,
        models.Wishlist.user_id == user_id
    ).first()

    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    return wishlist

# ========== Эндпоинты для событий ==========

# Получить список событий пользователя
@router.get("/", response_model=List[schemas.EventResponse])
def get_events(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    organized_events = db.query(models.Event).filter(
        models.Event.organizer_id == user_id
    ).all()

    participant_events = db.query(models.Event).join(
        models.EventParticipant,
        models.EventParticipant.event_id == models.Event.id
    ).filter(
        models.EventParticipant.user_id == user_id,
        models.Event.organizer_id != user_id
    ).all()

    all_events = list({event.id: event for event in organized_events + participant_events}.values())

    return all_events

# Создать событие
@router.post("/", response_model=schemas.EventResponse)
def create_event(
    event: schemas.EventCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db_event = models.Event(
        name=event.name,
        description=event.description,
        date=event.date,
        organizer_id=user_id
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event

# Получить детальную информацию о событии
@router.get("/{event_id}", response_model=schemas.EventDetailResponse)
def get_event_detail(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = check_event_access(db, event_id, user_id)

    organizer = get_user_by_id(db, event.organizer_id)

    participants = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id
    ).all()

    participants_data = []
    for p in participants:
        user = get_user_by_id(db, p.user_id)
        if user:
            participants_data.append(schemas.EventParticipantResponse(
                user_id=user.id,
                name=user.name,
                email=user.email
            ))

    event_wishlists = db.query(models.EventWishlist).filter(
        models.EventWishlist.event_id == event_id
    ).all()

    wishlists_data = []
    for ew in event_wishlists:
        wishlist = db.query(models.Wishlist).filter(
            models.Wishlist.id == ew.wishlist_id
        ).first()

        if wishlist:
            items_count = db.query(models.Item).filter(
                models.Item.wishlist_id == wishlist.id
            ).count()

            wishlists_data.append(schemas.EventWishlistResponse(
                wishlist_id=wishlist.id,
                wishlist_name=wishlist.name,
                items_count=items_count
            ))

    return schemas.EventDetailResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        date=event.date,
        organizer_id=event.organizer_id,
        organizer_name=organizer.name if organizer else "",
        participants=participants_data,
        wishlists=wishlists_data
    )

# Привязать вишлист к событию (только организатор)
@router.post("/{event_id}/wishlist", response_model=dict)
def attach_wishlist_to_event(
    event_id: int,
    wishlist_data: schemas.EventWishlistCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = get_event_or_404(db, event_id)

    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event organizer can attach wishlists"
        )

    wishlist = get_wishlist_or_404(db, wishlist_data.wishlist_id, user_id)

    existing = db.query(models.EventWishlist).filter(
        models.EventWishlist.event_id == event_id,
        models.EventWishlist.wishlist_id == wishlist_data.wishlist_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wishlist already attached to this event"
        )

    event_wishlist = models.EventWishlist(
        event_id=event_id,
        wishlist_id=wishlist_data.wishlist_id
    )

    db.add(event_wishlist)
    db.commit()

    return {
        "message": "Wishlist attached to event successfully",
        "event_id": event_id,
        "wishlist_id": wishlist_data.wishlist_id
    }

# Получить все вишлисты, привязанные к событию
@router.get("/{event_id}/wishlists", response_model=List[schemas.EventWishlistResponse])
def get_event_wishlists(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    check_event_access(db, event_id, user_id)

    event_wishlists = db.query(models.EventWishlist).filter(
        models.EventWishlist.event_id == event_id
    ).all()

    wishlists_data = []
    for ew in event_wishlists:
        wishlist = db.query(models.Wishlist).filter(
            models.Wishlist.id == ew.wishlist_id
        ).first()

        if wishlist:
            items_count = db.query(models.Item).filter(
                models.Item.wishlist_id == wishlist.id
            ).count()

            wishlists_data.append(schemas.EventWishlistResponse(
                wishlist_id=wishlist.id,
                wishlist_name=wishlist.name,
                items_count=items_count
            ))

    return wishlists_data

# Получить всех участников события
@router.get("/{event_id}/participants", response_model=List[schemas.EventParticipantResponse])
def get_event_participants(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    check_event_access(db, event_id, user_id)

    participants = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id
    ).all()

    participants_data = []
    for p in participants:
        user = get_user_by_id(db, p.user_id)
        if user:
            participants_data.append(schemas.EventParticipantResponse(
                user_id=user.id,
                name=user.name,
                email=user.email
            ))

    return participants_data

# Добавить участника в событие (только организатор)
@router.post("/{event_id}/participants/{participant_id}")
def add_participant_to_event(
    event_id: int,
    participant_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = get_event_or_404(db, event_id)

    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event organizer can add participants"
        )

    participant = get_user_by_id(db, participant_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    existing = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.user_id == participant_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant"
        )

    event_participant = models.EventParticipant(
        event_id=event_id,
        user_id=participant_id
    )

    db.add(event_participant)
    db.commit()

    return {
        "message": "Participant added successfully",
        "event_id": event_id,
        "participant_id": participant_id
    }

# Удалить событие (только организатор)
@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    event = get_event_or_404(db, event_id)

    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event organizer can delete the event"
        )

    db.delete(event)
    db.commit()

    return {"message": "Event deleted successfully"}

# Отвязать вишлист от события (только организатор)
@router.delete("/{event_id}/wishlist/{wishlist_id}")
def detach_wishlist_from_event(
    event_id: int,
    wishlist_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    event = get_event_or_404(db, event_id)

    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event organizer can detach wishlists"
        )

    event_wishlist = db.query(models.EventWishlist).filter(
        models.EventWishlist.event_id == event_id,
        models.EventWishlist.wishlist_id == wishlist_id
    ).first()

    if not event_wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist is not attached to this event"
        )

    db.delete(event_wishlist)
    db.commit()

    return {"message": "Wishlist detached from event successfully"}

# Удалить участника из события (только организатор)
@router.delete("/{event_id}/participants/{participant_id}")
def remove_participant_from_event(
    event_id: int,
    participant_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    event = get_event_or_404(db, event_id)

    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event organizer can remove participants"
        )

    if participant_id == event.organizer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove event organizer"
        )

    participant = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.user_id == participant_id
    ).first()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found in this event"
        )

    db.delete(participant)
    db.commit()

    return {"message": "Participant removed from event successfully"}
