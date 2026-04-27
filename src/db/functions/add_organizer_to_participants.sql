CREATE OR REPLACE FUNCTION add_organizer_to_participants()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO event_participants (event_id, user_id)
    VALUES (NEW.id, NEW.organizer_id)
    ON CONFLICT (event_id, user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
