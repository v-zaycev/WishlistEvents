# Setup

Run setup.sh from db folder:
```bash
cd ./db
./setup.sh
```

Create virtual environment
```bash
cd ../backend
python3 -m venv .venv
```
Activate virtual environmen
```bash
source .venv/bin/activate
```


Install requirements
```bash
pip install -r requirements.txt
```

Create .env file
```bash
echo -e "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/wishlist_events" > .env
```

# Run
Run ./run.sh from backend root folder
```bash
./run.sh
```
