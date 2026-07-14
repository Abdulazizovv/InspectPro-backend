"""
python manage.py seed_demo

Admin: +998901111111 / admin123
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


CLIENTS = [
    {"full_name": "Alisher Nazarov", "phone": "+998901234567"},
    {"full_name": "Bobur Karimov", "phone": "+998901234568"},
    {"full_name": "Dilnoza Yusupova", "phone": "+998901234569"},
    {"full_name": "Eldor Toshmatov", "phone": "+998901234570"},
    {"full_name": "Feruza Ergasheva", "phone": "+998901234571"},
    {"full_name": "Gulsanam Rahimova", "phone": "+998901234572"},
    {"full_name": "Hamza Abdullayev", "phone": "+998901234573"},
    {"full_name": "Iroda Mirzayeva", "phone": "+998901234574"},
]

VEHICLES = [
    {"brand": "Chevrolet", "model": "Cobalt", "year": 2021, "plate_number": "01A111AA", "engine_type": "gasoline", "color": "Oq"},
    {"brand": "Chevrolet", "model": "Nexia 3", "year": 2020, "plate_number": "10B222BB", "engine_type": "gasoline", "color": "Qora"},
    {"brand": "Chevrolet", "model": "Tracker", "year": 2023, "plate_number": "30C333CC", "engine_type": "gasoline", "color": "Kumush"},
    {"brand": "Toyota",    "model": "Camry",   "year": 2022, "plate_number": "70D444DD", "engine_type": "hybrid",   "color": "Qora"},
    {"brand": "Hyundai",   "model": "Accent",  "year": 2019, "plate_number": "22E555EE", "engine_type": "gasoline", "color": "Oq"},
    {"brand": "Kia",       "model": "Rio",     "year": 2021, "plate_number": "40F666FF", "engine_type": "gasoline", "color": "Qizil"},
    {"brand": "Chevrolet", "model": "Spark",   "year": 2018, "plate_number": "50G777GG", "engine_type": "gasoline", "color": "Sariq"},
    {"brand": "Daewoo",    "model": "Matiz",   "year": 2015, "plate_number": "60H888HH", "engine_type": "gasoline", "color": "Ko'k"},
    {"brand": "Chevrolet", "model": "Malibu",  "year": 2022, "plate_number": "01I999II", "engine_type": "gasoline", "color": "Kulrang"},
    {"brand": "Toyota",    "model": "Corolla", "year": 2020, "plate_number": "10J000JJ", "engine_type": "gasoline", "color": "Oq"},
    {"brand": "Hyundai",   "model": "Sonata",  "year": 2021, "plate_number": "30K111KK", "engine_type": "gasoline", "color": "Qora"},
    {"brand": "Kia",       "model": "K5",      "year": 2023, "plate_number": "70L222LL", "engine_type": "hybrid",   "color": "Oq"},
]


class Command(BaseCommand):
    help = "Demo ma'lumotlar bilan bazani to'ldiradi"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Avval bazani tozalaydi")

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        with transaction.atomic():
            admin = self._create_admin()
            clients = self._create_clients(admin)
            vehicles = self._create_vehicles(clients, admin)
            self._create_inspections(vehicles, admin)
            self._create_payments(clients, vehicles, admin)

        self.stdout.write(self.style.SUCCESS(
            "\n✓ Demo ma'lumotlar muvaffaqiyatli yaratildi!\n"
            "  Admin: +998901111111 / admin123\n"
            f"  Mijozlar: {len(clients)}\n"
            f"  Avtomobillar: {len(vehicles)}\n"
        ))

    def _clear(self):
        from apps.payments.models import Payment
        from apps.inspections.models import Inspection
        from apps.vehicles.models import Vehicle
        from apps.clients.models import Client

        Payment.objects.all().delete()
        Inspection.objects.all().delete()
        Vehicle.objects.all().delete()
        Client.objects.all().delete()
        self.stdout.write("  Baza tozalandi.")

    def _create_admin(self):
        from apps.accounts.models import User

        user, created = User.objects.get_or_create(
            phone="+998901111111",
            defaults={
                "email": "admin@inspectpro.uz",
                "full_name": "Admin InspectPro",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(f"  Admin yaratildi: {user.phone}")
        else:
            self.stdout.write(f"  Admin mavjud: {user.phone}")
        return user

    def _create_clients(self, admin):
        from apps.clients.models import Client

        clients = []
        for data in CLIENTS:
            client, created = Client.objects.get_or_create(
                phone=data["phone"],
                defaults={
                    "full_name": data["full_name"],
                    "is_active": True,
                    "created_by": admin,
                },
            )
            clients.append(client)
        self.stdout.write(f"  Mijozlar: {len(clients)} ta")
        return clients

    def _create_vehicles(self, clients, admin):
        from apps.vehicles.models import Vehicle

        today = date.today()
        vehicles = []
        for i, data in enumerate(VEHICLES):
            client = clients[i % len(clients)]

            # Turli muddatlar: o'tgan, yaqin, uzoq
            if i < 3:
                expiry = today - timedelta(days=random.randint(10, 90))   # muddati o'tgan
            elif i < 6:
                expiry = today + timedelta(days=random.randint(5, 28))    # yaqinlashayotgan
            else:
                expiry = today + timedelta(days=random.randint(60, 365))  # normal

            last_inspection = expiry - timedelta(days=365)

            v, created = Vehicle.objects.get_or_create(
                plate_number=data["plate_number"],
                defaults={
                    "client": client,
                    "brand": data["brand"],
                    "model": data["model"],
                    "year": data["year"],
                    "color": data["color"],
                    "engine_type": data["engine_type"],
                    "last_inspection_date": last_inspection,
                    "expiry_date": expiry,
                    "is_active": True,
                    "created_by": admin,
                },
            )
            vehicles.append(v)

        self.stdout.write(f"  Avtomobillar: {len(vehicles)} ta")
        return vehicles

    def _create_inspections(self, vehicles, admin):
        from apps.inspections.models import Inspection

        today = date.today()
        statuses = [Inspection.Status.PASSED, Inspection.Status.PASSED, Inspection.Status.FAILED, Inspection.Status.SCHEDULED]
        count = 0

        for v in vehicles:
            # Har bir avtomobil uchun 1-3 ta ko'rik
            for j in range(random.randint(1, 3)):
                days_ago = random.randint(0, 400)
                inspection_date = today - timedelta(days=days_ago)
                status = random.choice(statuses)

                expiry = None
                if status == Inspection.Status.PASSED:
                    expiry = inspection_date + timedelta(days=365)

                if not Inspection.objects.filter(vehicle=v, inspection_date=inspection_date).exists():
                    Inspection.objects.create(
                        vehicle=v,
                        inspection_date=inspection_date,
                        expiry_date=expiry,
                        status=status,
                        inspector=admin,
                        created_by=admin,
                        notes="Demo ko'rik" if j == 0 else "",
                    )
                    count += 1

        self.stdout.write(f"  Ko'riklar: {count} ta")

    def _create_payments(self, clients, vehicles, admin):
        from apps.clients.models import Client
        from apps.payments.models import Payment

        today = date.today()
        methods = [Payment.PaymentMethod.CASH, Payment.PaymentMethod.CARD, Payment.PaymentMethod.TRANSFER]
        statuses = [Payment.Status.PAID, Payment.Status.PAID, Payment.Status.PAID, Payment.Status.PENDING, Payment.Status.CANCELLED]
        amounts = [150_000, 200_000, 250_000, 300_000, 350_000, 400_000, 500_000]
        count = 0

        for client in clients:
            client_vehicles = [v for v in vehicles if v.client_id == client.id]
            for _ in range(random.randint(2, 5)):
                days_ago = random.randint(0, 180)
                payment_date = today - timedelta(days=days_ago)
                status = random.choice(statuses)

                Payment.objects.create(
                    client=client,
                    vehicle=random.choice(client_vehicles) if client_vehicles else None,
                    amount=Decimal(random.choice(amounts)),
                    payment_date=payment_date,
                    payment_method=random.choice(methods),
                    status=status,
                    created_by=admin,
                )
                count += 1

        self.stdout.write(f"  To'lovlar: {count} ta")
