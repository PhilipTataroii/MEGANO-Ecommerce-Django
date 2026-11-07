# MEGANO — Platformă de Comerț Electronic

🌐 **Limbi disponibile pentru documentație**

🇬🇧 [English](README.md) | 🇷🇺 [Русский](README.ru.md) | 🇷🇴 **Română**

## Prezentare generală

MEGANO este o aplicație web full-stack de comerț electronic, dezvoltată utilizând Python, Django și Django REST Framework.

Proiectul a fost realizat ca lucrare finală de diplomă în cadrul programului de formare profesională Python Developer oferit de Skillbox, în parteneriat cu GeekBrains.

Aplicația demonstrează competențe practice în dezvoltarea backend, proiectarea API-urilor REST, gestionarea bazelor de date, autentificarea utilizatorilor, procesarea comenzilor și testarea automată.

## Funcționalități

- Catalog de produse cu categorii și pagini detaliate
- Căutarea, filtrarea și sortarea produselor
- Înregistrarea, autentificarea și gestionarea profilurilor utilizatorilor
- Coș de cumpărături pentru vizitatori și utilizatori autentificați
- Crearea comenzilor și vizualizarea istoricului acestora
- Anularea comenzilor
- Flux de procesare a plăților
- Recenzii pentru produse
- Panou de administrare Django
- API REST cu documentație Swagger/OpenAPI
- Testare automată

## Tehnologii utilizate

### Backend

- Python
- Django 5.2
- Django REST Framework
- SQLite
- drf-spectacular

### Frontend

- HTML
- CSS
- JavaScript
- Django Templates

### Instrumente de dezvoltare

- Git
- GitLab
- PyCharm

## Structura proiectului

```text
django_diploma/
├── backend/
│   ├── accounts/
│   │   └── fixtures/
│   │       └── users.json
│   ├── basket/
│   ├── catalog/
│   ├── orders/
│   ├── config/
│   └── manage.py
├── diploma-frontend/
├── requirements.txt
├── README.md
├── README.ru.md
└── README.ro.md
```

## Instalare și pornire

### 1. Clonarea repository-ului

```bash
git clone https://gitlab.skillbox.ru/filip_tataroi/python_django_diploma.git
cd python_django_diploma
```

### 2. Crearea unui mediu virtual

```bash
python -m venv .venv
```

Activarea mediului virtual în Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

În Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Instalarea dependențelor

```bash
pip install -r requirements.txt
```

### 4. Instalarea pachetului frontend local

```bash
pip install -e ./diploma-frontend
```

### 5. Accesarea directorului backend

```bash
cd backend
```

### 6. Aplicarea migrațiilor bazei de date

```bash
python manage.py migrate
```

### 7. Încărcarea datelor demonstrative

```bash
python manage.py loaddata users
python manage.py loaddata catalog
```

Datele demonstrative includ două conturi:

| Nume utilizator | Rol |
|---|---|
| `demo_admin` | Administrator |
| `demo_customer` | Client |

Din motive de securitate, parolele sunt dezactivate în mod implicit.

Pentru configurarea parolelor la nivel local:

```bash
python manage.py changepassword demo_admin
python manage.py changepassword demo_customer
```

### 8. Pornirea serverului de dezvoltare

```bash
python manage.py runserver
```

După pornire, aplicația este disponibilă la adresa:

http://127.0.0.1:8000/

## Documentație API

**Documentație interactivă Swagger**

http://127.0.0.1:8000/api/docs/

**Schema OpenAPI**

http://127.0.0.1:8000/api/schema/

### Principalele endpoint-uri API

| Endpoint | Descriere |
|---|---|
| `/api/catalog` | Catalogul produselor |
| `/api/categories` | Categoriile produselor |
| `/api/product/<id>` | Detaliile produsului |
| `/api/basket` | Coșul de cumpărături |
| `/api/orders` | Gestionarea comenzilor |
| `/api/payment/<order_id>` | Procesarea plăților |
| `/api/products/popular` | Produse populare |
| `/api/products/limited` | Produse cu disponibilitate limitată |
| `/api/banners` | Bannere promoționale |

## Testare

Pentru executarea testelor automate din directorul backend:

```bash
python manage.py test
```

## Note privind dezvoltarea

Această aplicație reprezintă un proiect educațional destinat prezentării competențelor de programare într-un portofoliu profesional.

Configurația implicită este destinată dezvoltării locale.

Implementarea într-un mediu de producție necesită configurarea variabilelor de mediu securizate, a gazdelor permise, a fișierelor statice și a setărilor de securitate Django.

## Autor

**Filip Tataroi**

Dezvoltator Python / Django

**Tipul proiectului:** Proiect final de diplomă — Programul Python Developer, Skillbox

GitHub: https://github.com/PhilipTataroii

LinkedIn: https://www.linkedin.com/in/filip-tataroi/

## Licență

Proiectul a fost dezvoltat în scopuri educaționale și pentru prezentarea într-un portofoliu profesional. Nu se acordă o licență open-source decât dacă aceasta este adăugată explicit.
