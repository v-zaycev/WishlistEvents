from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db
from app.auth import get_user_by_id

router = APIRouter(prefix="/wishlists", tags=["wishlists"])

# ========== Вспомогательные функции ==========
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

def get_item_or_404(db: Session, item_id: int, wishlist_id: int):
    item = db.query(models.Item).filter(
        models.Item.id == item_id,
        models.Item.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item

# ========== Эндпоинты для вишлистов ==========

# Получить список вишлистов пользователя
@router.get("/", response_model=List[schemas.WishlistResponse])
def get_wishlists(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    wishlists = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == user_id
    ).all()

    return wishlists

# Создать новый вишлист
@router.post("/", response_model=schemas.WishlistResponse)
def create_wishlist(
    wishlist: schemas.WishlistCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db_wishlist = models.Wishlist(
        name=wishlist.name,
        user_id=user_id
    )

    db.add(db_wishlist)
    db.commit()
    db.refresh(db_wishlist)

    return db_wishlist

# Удалить вишлист
@router.delete("/{wishlist_id}")
def delete_wishlist(
    wishlist_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    wishlist = get_wishlist_or_404(db, wishlist_id, user_id)

    db.delete(wishlist)
    db.commit()

    return {"message": "Wishlist deleted successfully"}

# ========== Эндпоинты для позиций ==========

# Получить все позиции вишлиста
@router.get("/{wishlist_id}/items", response_model=List[schemas.ItemResponse])
def get_items(
    wishlist_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    get_wishlist_or_404(db, wishlist_id, user_id)

    items = db.query(models.Item).filter(
        models.Item.wishlist_id == wishlist_id
    ).all()

    return items

# Добавить позицию в вишлист
@router.post("/{wishlist_id}/items", response_model=schemas.ItemResponse)
def create_item(
    wishlist_id: int,
    item: schemas.ItemCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    get_wishlist_or_404(db, wishlist_id, user_id)

    db_item = models.Item(
        name=item.name,
        price=item.price,
        link=item.link,
        description=item.description,
        wishlist_id=wishlist_id
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item

# Удалить позицию из вишлиста
@router.delete("/{wishlist_id}/items/{item_id}")
def delete_item(
    wishlist_id: int,
    item_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    get_wishlist_or_404(db, wishlist_id, user_id)

    item = get_item_or_404(db, item_id, wishlist_id)

    db.delete(item)
    db.commit()

    return {"message": "Item deleted successfully"}

# Получить вишлист со всеми позициями
@router.get("/{wishlist_id}", response_model=schemas.WishlistWithItemsResponse)
def get_wishlist_with_items(
    wishlist_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    wishlist = get_wishlist_or_404(db, wishlist_id, user_id)

    items = db.query(models.Item).filter(
        models.Item.wishlist_id == wishlist_id
    ).all()

    return schemas.WishlistWithItemsResponse(
        id=wishlist.id,
        name=wishlist.name,
        user_id=wishlist.user_id,
        items=items
    )
