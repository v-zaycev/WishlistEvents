CREATE TRIGGER trigger_add_organizer
AFTER INSERT ON events
FOR EACH ROW
EXECUTE FUNCTION add_organizer_to_participants();
