from fastapi import FastAPI
from app.routers import (
    register_router,
    login_router,
    wishlists_router,
    events_router,
    bookings_router,
    expenses_router
)

app = FastAPI(
    title="WishlistEvents API",
    description="API for managing wishlists, events, and group gifting",
    version="1.0.0"
)

app.include_router(register_router)
app.include_router(login_router)
app.include_router(wishlists_router)
app.include_router(events_router)
app.include_router(bookings_router)
app.include_router(expenses_router)

@app.get("/")
def root():
    return {"message": "Welcome to WishlistEvents API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
