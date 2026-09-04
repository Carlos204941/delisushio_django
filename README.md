# Delisushio (Django)

A full-stack sushi delivery CRUD app built with Django, Poetry, and
Jinja2-rendered templates. This turns the models you provided into a working
storefront: browse products, add them to a cart, check out, and manage orders
end to end, with Django admin wired up for every app.

## Stack

- **Django 6.0**, **Poetry** for dependency management
- **Jinja2** templates for all customer-facing pages (via Django's built-in
  Jinja2 backend — see `config/jinja2_env.py`). Django's native template
  engine is kept alongside it for `django.contrib.admin` and the password
  reset emails.
- **PostgreSQL** database (required)
- **django-resized** for automatic product image resizing
- **djangorestframework** + **django-rest-passwordreset** for the OTP-based
  password reset signal handler you specified (a server-rendered fallback
  flow is also included so reset works without hitting the DRF API directly)

## Apps

| App                   | Models                                                      | What it covers                                                                                                                                    |
| --------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps.authentication` | `CustomUser`, `PasswordResetOTP`                            | register, login/logout, profile, 6-digit OTP password reset (two-step)                                                                            |
| `apps.products`       | `Product` (+ `Category`, `SpiceLevel` choices)              | menu listing with category filter, product detail, add-to-cart                                                                                    |
| `apps.orders`         | `DeliveryAddress`, `Cart`, `CartItem`, `Order`, `OrderItem` | cart management, delivery address CRUD, checkout (cart → order), full order CRUD (create via checkout, list/detail, status update, cancel/delete) |
| `apps.core`           | `BusinessHours`                                             | public hours page                                                                                                                                 |

Every model file matches what you provided verbatim; I only added a couple of
small conveniences (`Cart.total`/`item_count` properties, `Meta.ordering`,
`__str__` methods where missing) needed to make the templates and admin work.

## Getting started

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
poetry run python manage.py runserver
```

### Environment configuration

Copy `.env.example` values into your environment (or your preferred env loader):

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DB_ENGINE`
- `DJANGO_DB_NAME`
- `DJANGO_DB_USER`
- `DJANGO_DB_PASSWORD`
- `DJANGO_DB_HOST`
- `DJANGO_DB_PORT`
- `DJANGO_DB_CONN_MAX_AGE`
- `DJANGO_DB_SSLMODE` (optional)
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`
- `DJANGO_SECURE_REFERRER_POLICY`

For local development, defaults are permissive. For production, set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, restrictive hosts/origins, and HTTPS-related flags.

### PostgreSQL quick setup

Set these environment variables before running migrations:

- `DJANGO_DB_ENGINE=postgres`
- `DJANGO_DB_NAME=your_database`
- `DJANGO_DB_USER=your_user`
- `DJANGO_DB_PASSWORD=your_password`
- `DJANGO_DB_HOST=127.0.0.1`
- `DJANGO_DB_PORT=5432`

Then run:

```bash
poetry run python manage.py migrate
```

Then visit:

- `http://127.0.0.1:8000/` — storefront (menu)
- `http://127.0.0.1:8000/admin/` — Django admin (all four apps registered)
- `http://127.0.0.1:8000/accounts/register/` and `/accounts/login/`
- `http://127.0.0.1:8000/orders/cart/` and `/orders/checkout/`
- `http://127.0.0.1:8000/info/hours/`

To load some sample products, a superuser, and business hours, run:

```bash
poetry run python manage.py shell < seed_example.py
```

(A copy of the seed script used during development is included as
`seed_example.py` — feel free to delete it once you've got your own data.)

## URL map

```
/                                   products:list        (menu, GET, ?category=)
/<id>/                              products:detail       GET
/<id>/add-to-cart/                  products:add_to_cart  POST (login required)

/accounts/register/                 authentication:register
/accounts/login/                    authentication:login
/accounts/logout/                   authentication:logout
/accounts/profile/                  authentication:profile
/accounts/password-reset/           authentication:password_reset_request
/accounts/password-reset/confirm/   authentication:password_reset_confirm

/orders/cart/                       orders:cart
/orders/cart/item/<id>/update/      orders:cart_item_update   POST
/orders/cart/item/<id>/remove/      orders:cart_item_remove   POST
/orders/addresses/                  orders:address_list
/orders/addresses/new/              orders:address_create
/orders/addresses/<id>/edit/        orders:address_update
/orders/addresses/<id>/delete/      orders:address_delete
/orders/checkout/                   orders:checkout            (Create: cart -> Order)
/orders/                            orders:list                (Read: list)
/orders/<uuid>/                     orders:detail              (Read: detail)
/orders/<uuid>/edit/                orders:update              (Update: status)
/orders/<uuid>/delete/              orders:delete              (Delete/cancel)

/info/                              core:home
/info/hours/                        core:hours

/api/password_reset/*               django-rest-passwordreset DRF API
                                     (triggers the OTP email via the signal
                                     in apps/authentication/signals.py)
```

## Design decisions & notes

- **Cart → Order flow**: `CartItem` stores a snapshot of the product name and
  category at add-time (as your model defines); at checkout, that snapshot
  plus the _current_ product price is copied into `OrderItem`, and
  `Order.calculate_total()` sums it up. The cart is cleared after a
  successful checkout.
- **Order CRUD boundaries**: an order can be edited (status) or
  cancelled/deleted only while it's `PENDING` or `CONFIRMED`. `DELIVERED`
  orders are locked; `PENDING` orders are hard-deleted on cancel, anything
  further along is soft-cancelled (status set to `CANCELLED`) instead of
  deleted, so the order history stays intact.
- **Password reset** ships two overlapping paths, matching what your model
  comments call out (six-digit OTP, brute-force protection via
  `attempts`/`max_attempts`, single-use codes):
  - A server-rendered two-step flow (`/accounts/password-reset/` →
    `/accounts/password-reset/confirm/`) that works directly against the
    Jinja2 templates.
  - The DRF-based flow via `django-rest-passwordreset` (`/api/password_reset/`)
    which triggers `apps/authentication/signals.py` and emails the same kind
    of OTP. Useful if you're driving this from a JS frontend or mobile app
    later.
  - In dev, `EMAIL_BACKEND` is the console backend, so reset codes print to
    the terminal instead of actually sending email.
- **Jinja2 auth/CSRF**: Django's Jinja2 backend doesn't provide the
  `{% csrf_token %}` template tag, so every form does
  `<input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf_token }}">`
  instead — same effect, just spelled the Jinja2 way.
- **Image uploads**: `MEDIA_URL`/`MEDIA_ROOT` are configured and served in
  `DEBUG` mode; wire up real static/media hosting (S3, etc.) before deploying.

## Before deploying

- Set `DEBUG = False`, a real `SECRET_KEY` (env var), and a real
  `ALLOWED_HOSTS` list in `config/settings.py` — right now it's opened up to
  `localhost`/`127.0.0.1`/`testserver` for local dev and testing.
- Ensure PostgreSQL is reachable with the configured `DJANGO_DB_*` variables.
- Configure a real `EMAIL_BACKEND` (SMTP/SES/SendGrid/etc.) so password
  reset emails actually go out.
