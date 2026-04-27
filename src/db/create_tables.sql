-- 1. Таблица пользователей
CREATE TABLE users (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- 2. Таблица вишлистов
CREATE TABLE wishlists (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Таблица событий
CREATE TABLE events (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    organizer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Таблица подарков/позиций
CREATE TABLE items (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2),
    link VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    wishlist_id INTEGER NOT NULL REFERENCES wishlists(id) ON DELETE CASCADE,
    booked_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    booked_event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
    CONSTRAINT unique_booking_per_event UNIQUE (id, booked_event_id)
);

-- 5. Связь событий с вишлистами
CREATE TABLE event_wishlists (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    wishlist_id INTEGER NOT NULL REFERENCES wishlists(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, wishlist_id)
);

-- 6. Участники событий
CREATE TABLE event_participants (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, user_id)
);

-- 7. Таблица трат
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    total_amount DECIMAL(10, 2) NOT NULL,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    paid_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- 8. Доли расходов
CREATE TABLE expense_shares (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    amount DECIMAL(10, 2) NOT NULL,
    is_paid BOOLEAN DEFAULT FALSE,
    expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(expense_id, user_id)
);

CREATE INDEX idx_items_wishlist_id ON items(wishlist_id);
CREATE INDEX idx_items_booked_by ON items(booked_by);
CREATE INDEX idx_items_booked_event ON items(booked_event_id);
CREATE INDEX idx_events_organizer ON events(organizer_id);
CREATE INDEX idx_events_date ON events(date);
CREATE INDEX idx_event_participants_user ON event_participants(user_id);
CREATE INDEX idx_expenses_event ON expenses(event_id);
CREATE INDEX idx_expense_shares_user ON expense_shares(user_id);
CREATE INDEX idx_expense_shares_expense ON expense_shares(expense_id);
