# BDS - Database Application (Flask & PostgreSQL)

Implementace databázové aplikace pro správu e-shopu. Jádro je postaveno na **Flask** frameworku s využitím **PostgreSQL** pro perzistenci dat. Projekt demonstruje bezpečné ukládání hesel pomocí Argon2, prevenci SQL Injection, transakční zpracování a pokročilé SQL operace.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.x-green)
![PostgreSQL](https://img.shields.io/badge/postgresql-15%2B-blue)
![License](https://img.shields.io/badge/license-MIT-orange)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

Kód je navržen tak, aby splňoval požadavky na bezpečný vývoj aplikací, oddělení vrstev (MVC/MTV) a testovatelnost pomocí in-memory databází.

## Quickstart

Tato aplikace vyžaduje Python 3 a běžící instanci PostgreSQL.

### 1. Instalace a Příprava

Nejprve naklonujte repozitář a připravte virtuální prostředí:

```bash
# Vytvoření venv
python3 -m venv venv

# Aktivace (Linux/Mac)
source venv/bin/activate
# Aktivace (Windows)
# venv\Scripts\activate

# Instalace závislostí
pip install -r requirements.txt
```

### 2. Konfigurace Databáze

Vytvořte soubor `.env` v kořenovém adresáři (dle přiloženého `.env.template`):

```ini
DB_USER=uzivatel
DB_PASSWORD=heslo
DB_HOST=hostname, adress
DB_PORT=5432
DB_NAME=bds_db
SECRET_KEY=tajny_klic_flask
```

Následně inicializujte databázové schéma:

```bash
psql -U postgres -d bds_db -f sql_scripts/ddl_schema.sql
```

### 3. Generování SSL a Spuštění

Pro bezpečný HTTPS provoz vygenerujte self-signed certifikát:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Spusťte aplikaci:

```bash
python run.py
```

Aplikace nyní běží na `https://localhost:443`.

## Popis Funkcionality

Následující API a moduly jsou implementovány pro správu e-shopu.

### Správa Entit (CRUD)
Aplikace poskytuje kompletní rozhraní pro správu:
* **Produkty & Kategorie:** Včetně řazení, filtrování a uploadu obrázků.
* **Zákazníci & Zaměstnanci:** Správa profilů a rolí.
* **Objednávky:** Komplexní proces tvorby objednávky.

### Transakční Zpracování
Operace, které mění více tabulek najednou, jsou baleny do atomických transakcí.

```python
try:
    # Vytvoření hlavičky objednávky
    db.session.add(new_order)
    db.session.flush()
    
    # Vložení položek
    db.session.add(item)
    
    # Potvrzení transakce
    db.session.commit()
except Exception:
    # Rollback při chybě
    db.session.rollback()
```

## Security Analysis

Bezpečnost byla prioritou při návrhu této aplikace. Níže jsou rozebrány klíčové mechanismy.

### Password Hashing (Argon2)
Místo zastaralých metod (MD5, SHA1) nebo pomalejších (PBKDF2, BCrypt) využíváme **Argon2**.
Argon2 je vítězem *Password Hashing Competition* a poskytuje nejlepší ochranu proti GPU/ASIC útokům díky memory-hard designu.

> "Argon2 is the modern standard for password hashing, providing superior resistance against trade-off attacks."

### Prevence SQL Injection
Aplikace striktně využívá **Prepared Statements** (via SQLAlchemy) pro veškerou interakci s databází.
V projektu je zahrnuta sekce **SQLi Demo**, která demonstruje rozdíl mezi zranitelným a bezpečným kódem.

* **Zranitelný:** `SELECT * FROM users WHERE user = '` + `input` + `'`
* **Bezpečný:** `SELECT * FROM users WHERE user = :input`

### Ochrana citlivých údajů
Telefonní čísla zákazníků jsou v databázi šifrována pomocí `pgp_sym_encrypt` (rozšíření `pgcrypto`), což zajišťuje ochranu dat "at rest".

## Tech Stack

* **Jazyk:** Python 3.10+
* **Backend:** Flask 3.x, Werkzeug
* **ORM:** SQLAlchemy 2.0
* **Databáze:** PostgreSQL 15+ (včetně rozšíření `pgcrypto`)
* **Bezpečnost:** Argon2-cffi, Flask-Login, OpenSSL
* **Frontend:** Jinja2, Bootstrap 5, jQuery

## Testování

Projekt obsahuje sadu Unit testů běžících nad in-memory SQLite databází, které ověřují integritu datového modelu a CRUD operací bez nutnosti běhu ostré DB.

Spuštění testů:

```bash
python3 -m unittest discover tests
```

## License

Copyright 2025 Kryštof Trojak

Tento projekt je licencován pod licencí **MIT**.
Seznam použitých knihoven třetích stran a jejich licencí naleznete v souboru [LICENSES.md](LICENSES.md).