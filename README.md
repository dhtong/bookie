# How to run

step 1: install python3 and pip

step 2: start virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
```

step 3: install python dependencies

```
pip install -r requirements.txt
```

step 4: set up config

```
cp example_configs.json configs.json
// set up dates and airports short codes that you want to search for
// set up your notification recipient email in configs.json (optional)

cp example_email_config.json email_config.json
// gmail *app* password in email_config.json (optional)
```
step 5: run the script

```
python book.py
```

# How to read
example:
```
Flight(date=2025-06-26, AMS ====> ATL, has_business) // there is a flight from AMS to ATL on 2025-06-26 with business class
Flight(date=2025-06-19, VCE ====> ATL) // there is a flight from VCE to ATL on 2025-06-19
```

