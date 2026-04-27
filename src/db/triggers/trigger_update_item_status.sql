CREATE OR REPLACE FUNCTION update_item_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.booked_by IS NOT NULL AND OLD.booked_by IS NULL THEN
        NEW.status := 'booked';
    ELSIF NEW.booked_by IS NULL AND OLD.booked_by IS NOT NULL THEN
        NEW.status := 'active';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_item_status
BEFORE UPDATE ON items
FOR EACH ROW
EXECUTE FUNCTION update_item_status();
