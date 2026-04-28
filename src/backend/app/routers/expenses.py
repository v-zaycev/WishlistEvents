from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app import schemas, models
from app.database import get_db
from app.auth import get_user_by_id

router = APIRouter(prefix="/events", tags=["expenses"])

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

# Рассчитать балансы участников события
def calculate_balances(db: Session, event_id: int) -> List[schemas.UserBalanceResponse]:
    participants = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id
    ).all()

    balances = []

    for participant in participants:
        user = get_user_by_id(db, participant.user_id)
        if not user:
            continue

        paid_expenses = db.query(models.Expense).filter(
            models.Expense.event_id == event_id,
            models.Expense.paid_by == participant.user_id
        ).with_entities(models.Expense.total_amount).all()
        total_paid = sum(float(p[0]) for p in paid_expenses) if paid_expenses else 0.0

        shares = db.query(models.ExpenseShare).join(
            models.Expense, models.Expense.id == models.ExpenseShare.expense_id
        ).filter(
            models.Expense.event_id == event_id,
            models.ExpenseShare.user_id == participant.user_id
        ).with_entities(models.ExpenseShare.amount).all()
        total_owes = sum(float(s[0]) for s in shares) if shares else 0.0

        paid_shares = db.query(models.ExpenseShare).join(
            models.Expense, models.Expense.id == models.ExpenseShare.expense_id
        ).filter(
            models.Expense.event_id == event_id,
            models.ExpenseShare.user_id == participant.user_id,
            models.ExpenseShare.is_paid == True
        ).with_entities(models.ExpenseShare.amount).all()
        total_paid_shares = sum(float(s[0]) for s in paid_shares) if paid_shares else 0.0

        remaining_debt = total_owes - total_paid_shares
        balance = total_paid - remaining_debt

        balances.append(schemas.UserBalanceResponse(
            user_id=user.id,
            user_name=user.name,
            paid=round(total_paid, 2),
            owes=round(remaining_debt, 2),
            balance=round(balance, 2)
        ))

    return balances


# ========== Эндпоинты для расходов ==========

# Получить список трат и долгов участников события
@router.get("/{event_id}/expenses", response_model=schemas.EventExpensesResponse)
def get_event_expenses(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    check_event_access(db, event_id, user_id)

    expenses = db.query(models.Expense).filter(
        models.Expense.event_id == event_id
    ).all()

    expenses_data = []
    for expense in expenses:
        paid_by_name = None
        if expense.paid_by:
            payer = get_user_by_id(db, expense.paid_by)
            paid_by_name = payer.name if payer else None

        expenses_data.append(schemas.ExpenseResponse(
            id=expense.id,
            name=expense.name,
            description=expense.description,
            total_amount=float(expense.total_amount),
            event_id=expense.event_id,
            paid_by=expense.paid_by,
            paid_by_name=paid_by_name
        ))

    balances = calculate_balances(db, event_id)

    return schemas.EventExpensesResponse(
        expenses=expenses_data,
        balances=balances
    )

# Получить детальную информацию о трате (с долями)
@router.get("/{event_id}/expenses/{expense_id}", response_model=schemas.ExpenseDetailResponse)
def get_expense_detail(
    event_id: int,
    expense_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    check_event_access(db, event_id, user_id)

    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.event_id == event_id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    shares = db.query(models.ExpenseShare).filter(
        models.ExpenseShare.expense_id == expense_id
    ).all()

    shares_data = []
    for share in shares:
        user = get_user_by_id(db, share.user_id)
        if user:
            shares_data.append(schemas.ExpenseShareResponse(
                user_id=user.id,
                user_name=user.name,
                amount=float(share.amount),
                is_paid=share.is_paid
            ))

    paid_by_name = None
    if expense.paid_by:
        payer = get_user_by_id(db, expense.paid_by)
        paid_by_name = payer.name if payer else None

    return schemas.ExpenseDetailResponse(
        id=expense.id,
        name=expense.name,
        description=expense.description,
        total_amount=float(expense.total_amount),
        paid_by=expense.paid_by,
        paid_by_name=paid_by_name,
        shares=shares_data
    )

# Добавить общую трату (автоматическое распределение долей)
@router.post("/{event_id}/expenses", response_model=schemas.ExpenseResponse)
def create_expense(
    event_id: int,
    expense: schemas.ExpenseCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    event = check_event_access(db, event_id, user_id)

    payer = get_user_by_id(db, user_id)
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    participants = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id
    ).all()

    if not participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event has no participants"
        )

    participant_count = len(participants)

    share_amount = expense.total_amount / participant_count

    db_expense = models.Expense(
        name=expense.name,
        description=expense.description,
        total_amount=expense.total_amount,
        event_id=event_id,
        paid_by=user_id
    )

    db.add(db_expense)
    db.flush()

    for participant in participants:

        db_share = models.ExpenseShare(
            amount=share_amount,
            is_paid=False,
            expense_id=db_expense.id,
            user_id=participant.user_id
        )
        db.add(db_share)

    db.commit()
    db.refresh(db_expense)

    return schemas.ExpenseResponse(
        id=db_expense.id,
        name=db_expense.name,
        description=db_expense.description,
        total_amount=float(db_expense.total_amount),
        event_id=db_expense.event_id,
        paid_by=db_expense.paid_by,
        paid_by_name=payer.name
    )

# Отметить долю пользователя как оплаченную
@router.put("/{event_id}/expenses/{expense_id}/pay")
def mark_share_as_paid(
    event_id: int,
    expense_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    check_event_access(db, event_id, user_id)

    share = db.query(models.ExpenseShare).join(
        models.Expense, models.Expense.id == models.ExpenseShare.expense_id
    ).filter(
        models.Expense.event_id == event_id,
        models.Expense.id == expense_id,
        models.ExpenseShare.user_id == user_id
    ).first()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )

    if share.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Share already marked as paid"
        )

    share.is_paid = True
    db.commit()

    return {"message": "Share marked as paid successfully"}

# Получить балансы участников события
@router.get("/{event_id}/balances", response_model=List[schemas.UserBalanceResponse])
def get_event_balances(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    check_event_access(db, event_id, user_id)

    balances = calculate_balances(db, event_id)

    return balances
