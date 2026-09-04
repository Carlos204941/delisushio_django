import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.authentication.models import CustomUser
from apps.products.models import Product, Category, SpiceLevel
from apps.core.models import BusinessHours

if not CustomUser.objects.filter(email='admin@delisushio.local').exists():
    CustomUser.objects.create_superuser(email='admin@delisushio.local', password='DelisushioAdmin123!')
    print('Superuser created')

if not Product.objects.exists():
    Product.objects.create(category=Category.RAW_FISH, name='Salmon Nigiri (2pc)', description='Fresh salmon over seasoned rice.', price=6.50, stock_quantity=40, spice_level=SpiceLevel.NONE, allergens=['fish'])
    Product.objects.create(category=Category.POKE_BOWL, name='Spicy Tuna Poke Bowl', description='Tuna, rice, edamame, spicy mayo.', price=13.75, stock_quantity=25, spice_level=SpiceLevel.MEDIUM, allergens=['fish', 'soy'])
    Product.objects.create(category=Category.VEGETARIAN, name='Avocado Cucumber Roll', description='Classic veggie roll, 8 pieces.', price=7.00, stock_quantity=30, spice_level=SpiceLevel.NONE, allergens=[])
    Product.objects.create(category=Category.HARUMAKI, name='Vegetable Harumaki (4pc)', description='Crispy fried spring rolls.', price=5.50, stock_quantity=20, spice_level=SpiceLevel.MILD, allergens=['gluten'])
    print('Products seeded')

if not BusinessHours.objects.exists():
    for day in range(7):
        BusinessHours.objects.create(day_of_week=day, is_open=(day != 0), opening_time='11:00', closing_time='21:30')
    print('Business hours seeded')
