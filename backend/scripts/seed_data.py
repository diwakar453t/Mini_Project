"""
Seed script to populate database with sample data
"""
import random
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from faker import Faker
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, Profile, UserRole, KYCStatus
from app.models.charger import Charger, ChargerPricing, ConnectorType, ChargerType, ChargerStatus, PricingType
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.review import Review
from app.core.database import Base

fake = Faker('en_IN')  # Indian locale
Faker.seed(42)  # For reproducible data
random.seed(42)

# Indian cities with coordinates
INDIAN_CITIES = [
    {"name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
    {"name": "Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
    {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
    {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867},
    {"name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567},
    {"name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
    {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639},
    {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873},
    {"name": "Kochi", "state": "Kerala", "lat": 9.9312, "lng": 76.2673},
    {"name": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lng": 75.8577},
    {"name": "Chandigarh", "state": "Punjab", "lat": 30.7333, "lng": 76.7794},
    {"name": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lng": 76.9558},
    {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462},
    {"name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lng": 85.8245},
]

# Sample vehicle types
VEHICLE_TYPES = [
    "Tata Nexon EV", "MG ZS EV", "Hyundai Kona Electric", "Mahindra e2o Plus",
    "Ather 450X", "Bajaj Chetak Electric", "TVS iQube Electric", "Hero Electric Optima"
]

# Sample amenities and features
AMENITIES = ["parking", "wifi", "restroom", "security", "cafe", "shelter"]
FEATURES = ["cable_provided", "weatherproof", "app_control", "rfid_access", "payment_terminal"]

# Sample positive/negative aspects for reviews
POSITIVE_ASPECTS = [
    "fast_charging", "clean_location", "helpful_host", "easy_access", "good_parking",
    "safe_area", "well_maintained", "clear_instructions", "responsive_host", "fair_pricing"
]

NEGATIVE_ASPECTS = [
    "slow_charging", "hard_to_find", "no_parking", "poor_maintenance", "expensive",
    "unsafe_area", "unresponsive_host", "unclear_instructions", "dirty_location"
]


def create_engine_and_session():
    """Create database engine and session"""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal()


def create_admin_user(db):
    """Create admin user"""
    admin = User(
        email=settings.ADMIN_EMAIL,
        phone="+919876543210",
        phone_verified=True,
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        name="ChargeMitra Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        kyc_status=KYCStatus.VERIFIED,
        email_verified=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    # Create admin profile
    admin_profile = Profile(
        user_id=admin.id,
        bio="Platform Administrator",
        city="Mumbai",
        state="Maharashtra",
        country="India",
    )
    db.add(admin_profile)
    print(f"✅ Created admin user: {admin.email}")
    return admin


def create_test_users(db):
    """Create test host and renter accounts"""
    # Test Host
    test_host = User(
        email=settings.TEST_HOST_EMAIL,
        phone="+919876543211",
        phone_verified=True,
        hashed_password=get_password_hash(settings.TEST_HOST_PASSWORD),
        name="Test Host",
        role=UserRole.HOST,
        is_active=True,
        is_verified=True,
        kyc_status=KYCStatus.VERIFIED,
        email_verified=True,
    )
    db.add(test_host)
    
    # Test Renter
    test_renter = User(
        email=settings.TEST_RENTER_EMAIL,
        phone="+919876543212",
        phone_verified=True,
        hashed_password=get_password_hash(settings.TEST_RENTER_PASSWORD),
        name="Test Renter",
        role=UserRole.RENTER,
        is_active=True,
        is_verified=True,
        kyc_status=KYCStatus.VERIFIED,
        email_verified=True,
    )
    db.add(test_renter)
    db.commit()
    
    # Create profiles
    for user in [test_host, test_renter]:
        db.refresh(user)
        profile = Profile(
            user_id=user.id,
            city="Mumbai",
            state="Maharashtra",
            country="India",
            vehicle_details={
                "type": random.choice(VEHICLE_TYPES),
                "year": random.randint(2020, 2024),
            } if user.role == UserRole.RENTER else None
        )
        db.add(profile)
    
    db.commit()
    print(f"✅ Created test users: {test_host.email}, {test_renter.email}")
    return test_host, test_renter


def create_users(db, count=100):
    """Create sample users"""
    users = []
    
    for i in range(count):
        city_data = random.choice(INDIAN_CITIES)
        is_host = i < 10  # First 10 users are hosts
        
        user = User(
            email=fake.email(),
            phone=f"+91{random.randint(7000000000, 9999999999)}",
            phone_verified=random.choice([True, False]),
            hashed_password=get_password_hash("password123"),
            name=fake.name(),
            role=UserRole.HOST if is_host else UserRole.RENTER,
            is_active=True,
            is_verified=random.choice([True, False]),
            kyc_status=random.choice([KYCStatus.VERIFIED, KYCStatus.PENDING, KYCStatus.SUBMITTED]),
            email_verified=random.choice([True, False]),
        )
        
        db.add(user)
        users.append(user)
    
    db.commit()
    
    # Create profiles
    for user in users:
        db.refresh(user)
        city_data = random.choice(INDIAN_CITIES)
        
        profile = Profile(
            user_id=user.id,
            bio=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
            city=city_data["name"],
            state=city_data["state"],
            country="India",
            pincode=fake.postcode(),
            address=fake.address(),
            host_rating=str(round(random.uniform(3.0, 5.0), 1)) if user.role == UserRole.HOST else "0.0",
            host_rating_count=random.randint(0, 50) if user.role == UserRole.HOST else 0,
            vehicle_details={
                "type": random.choice(VEHICLE_TYPES),
                "year": random.randint(2018, 2024),
                "battery_capacity": random.randint(25, 75),
            } if user.role == UserRole.RENTER else None,
            preferred_connectors=random.sample([e.value for e in ConnectorType], random.randint(1, 3)) if user.role == UserRole.RENTER else None,
        )
        db.add(profile)
    
    db.commit()
    print(f"✅ Created {count} users")
    return users


def create_chargers(db, hosts, count=50):
    """Create sample chargers"""
    chargers = []
    
    # Filter only host users
    host_users = [u for u in hosts if u.role == UserRole.HOST]
    
    for i in range(count):
        host = random.choice(host_users)
        city_data = random.choice(INDIAN_CITIES)
        
        # Add some variation to coordinates for multiple chargers per city
        lat_offset = random.uniform(-0.1, 0.1)
        lng_offset = random.uniform(-0.1, 0.1)
        lat = city_data["lat"] + lat_offset
        lng = city_data["lng"] + lng_offset
        
        charger = Charger(
            host_id=host.id,
            title=f"{fake.company()} Charging Station",
            description=fake.text(max_nb_chars=300),
            address=fake.address(),
            city=city_data["name"],
            state=city_data["state"],
            pincode=fake.postcode(),
            latitude=lat,
            longitude=lng,
            connector_type=random.choice(list(ConnectorType)),
            charger_type=random.choice(list(ChargerType)),
            max_power_kw=random.choice([3.7, 7, 11, 22, 50, 120, 150]),
            voltage=random.choice([220, 400, 480]),
            current_rating=random.choice([16, 32, 63, 125]),
            images=[f"/images/charger_{i}_{j}.jpg" for j in range(random.randint(1, 4))],
            cover_image=f"/images/charger_{i}_cover.jpg",
            amenities={amenity: random.choice([True, False]) for amenity in AMENITIES},
            features={feature: random.choice([True, False]) for feature in FEATURES},
            availability_schedule={
                "monday": {"start": "06:00", "end": "22:00", "available": True},
                "tuesday": {"start": "06:00", "end": "22:00", "available": True},
                "wednesday": {"start": "06:00", "end": "22:00", "available": True},
                "thursday": {"start": "06:00", "end": "22:00", "available": True},
                "friday": {"start": "06:00", "end": "22:00", "available": True},
                "saturday": {"start": "08:00", "end": "20:00", "available": True},
                "sunday": {"start": "08:00", "end": "20:00", "available": random.choice([True, False])},
            },
            is_active=True,
            is_verified=random.choice([True, False]),
            auto_accept_bookings=random.choice([True, False]),
            current_status=random.choice([ChargerStatus.AVAILABLE, ChargerStatus.IN_USE, ChargerStatus.MAINTENANCE]),
            access_instructions=fake.text(max_nb_chars=200),
            total_bookings=random.randint(0, 100),
            total_energy_delivered=random.uniform(1000, 50000),
            average_rating=round(random.uniform(3.0, 5.0), 1),
            rating_count=random.randint(0, 50),
        )
        
        db.add(charger)
        chargers.append(charger)
    
    db.commit()
    
    # Create pricing for chargers
    for charger in chargers:
        db.refresh(charger)
        
        pricing_type = random.choice(list(PricingType))
        base_price = {
            PricingType.PER_HOUR: random.uniform(50, 200),
            PricingType.PER_KWH: random.uniform(8, 25),
            PricingType.FLAT_RATE: random.uniform(100, 500),
        }[pricing_type]
        
        pricing = ChargerPricing(
            charger_id=charger.id,
            pricing_type=pricing_type,
            price_value=base_price,
            min_session_minutes=random.choice([15, 30, 60]),
            max_session_minutes=random.choice([240, 360, 480]),
            peak_hours_start="09:00" if random.choice([True, False]) else None,
            peak_hours_end="18:00" if random.choice([True, False]) else None,
            peak_price_multiplier=random.uniform(1.2, 1.5),
            weekend_price_multiplier=random.uniform(0.9, 1.3),
            booking_fee=random.uniform(0, 20),
            overstay_fee_per_hour=random.uniform(50, 100),
            late_cancellation_fee=random.uniform(50, 200),
            advance_booking_hours=random.choice([24, 48, 168]),
            same_day_booking=random.choice([True, False]),
        )
        db.add(pricing)
    
    db.commit()
    print(f"✅ Created {count} chargers with pricing")
    return chargers


def create_bookings(db, chargers, users, count=200):
    """Create sample bookings"""
    bookings = []
    renters = [u for u in users if u.role == UserRole.RENTER]
    
    for i in range(count):
        charger = random.choice(chargers)
        renter = random.choice(renters)
        
        # Generate booking time (mix of past and future)
        base_date = datetime.utcnow() - timedelta(days=random.randint(-30, 30))
        start_time = base_date.replace(
            hour=random.randint(6, 20),
            minute=random.choice([0, 15, 30, 45]),
            second=0,
            microsecond=0
        )
        duration_hours = random.uniform(1, 8)
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Calculate cost based on pricing
        pricing = db.query(ChargerPricing).filter(ChargerPricing.charger_id == charger.id).first()
        if pricing:
            if pricing.pricing_type == PricingType.PER_HOUR:
                subtotal = duration_hours * pricing.price_value
            elif pricing.pricing_type == PricingType.PER_KWH:
                estimated_kwh = duration_hours * charger.max_power_kw * 0.8
                subtotal = estimated_kwh * pricing.price_value
            else:
                subtotal = pricing.price_value
            
            platform_fee = subtotal * 0.15  # 15% commission
            total_amount = subtotal + platform_fee + pricing.booking_fee
        else:
            subtotal = duration_hours * 100  # Fallback pricing
            platform_fee = subtotal * 0.15
            total_amount = subtotal + platform_fee
        
        # Determine status based on timing
        now = datetime.utcnow()
        if start_time > now:
            status = random.choice([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            payment_status = PaymentStatus.COMPLETED if status == BookingStatus.CONFIRMED else PaymentStatus.PENDING
        elif end_time < now:
            status = random.choice([BookingStatus.COMPLETED, BookingStatus.CANCELLED])
            payment_status = PaymentStatus.COMPLETED if status == BookingStatus.COMPLETED else random.choice([PaymentStatus.REFUNDED, PaymentStatus.FAILED])
        else:
            status = BookingStatus.ACTIVE
            payment_status = PaymentStatus.COMPLETED
        
        booking = Booking(
            charger_id=charger.id,
            renter_id=renter.id,
            start_time=start_time,
            end_time=end_time,
            estimated_duration_minutes=int(duration_hours * 60),
            status=status,
            payment_status=payment_status,
            booking_code=f"BK{random.randint(100000, 999999)}",
            pricing_type=pricing.pricing_type.value if pricing else "per_hour",
            unit_price=pricing.price_value if pricing else 100,
            estimated_cost=subtotal,
            subtotal=subtotal,
            platform_fee=platform_fee,
            total_amount=total_amount,
            paid_amount=total_amount if payment_status == PaymentStatus.COMPLETED else 0,
            currency="INR",
            payment_method=random.choice(["razorpay", "upi", "stripe"]) if payment_status == PaymentStatus.COMPLETED else None,
            vehicle_info={
                "type": random.choice(VEHICLE_TYPES),
                "battery_capacity": f"{random.randint(25, 75)}%",
            },
            confirmed_at=start_time - timedelta(hours=random.randint(1, 24)) if status != BookingStatus.PENDING else None,
            completed_at=end_time if status == BookingStatus.COMPLETED else None,
            cancelled_at=start_time - timedelta(hours=random.randint(1, 12)) if status == BookingStatus.CANCELLED else None,
        )
        
        db.add(booking)
        bookings.append(booking)
    
    db.commit()
    print(f"✅ Created {count} bookings")
    return bookings


def create_reviews(db, bookings):
    """Create sample reviews for completed bookings"""
    completed_bookings = [b for b in bookings if b.status == BookingStatus.COMPLETED]
    reviews_count = min(len(completed_bookings), random.randint(50, 100))
    
    sample_bookings = random.sample(completed_bookings, reviews_count)
    
    for booking in sample_bookings:
        rating = random.randint(3, 5)  # Bias towards positive reviews
        
        review = Review(
            booking_id=booking.id,
            charger_id=booking.charger_id,
            reviewer_id=booking.renter_id,
            rating=rating,
            title=fake.sentence(nb_words=4),
            comment=fake.text(max_nb_chars=300) if random.choice([True, False]) else None,
            charger_condition_rating=random.randint(rating-1, 5) if rating > 1 else rating,
            location_rating=random.randint(rating-1, 5) if rating > 1 else rating,
            host_communication_rating=random.randint(rating-1, 5) if rating > 1 else rating,
            value_for_money_rating=random.randint(rating-1, 5) if rating > 1 else rating,
            charging_speed_rating=random.randint(rating-1, 5) if rating > 1 else rating,
            positive_aspects=random.sample(POSITIVE_ASPECTS, random.randint(1, 3)) if rating >= 4 else [],
            negative_aspects=random.sample(NEGATIVE_ASPECTS, random.randint(1, 2)) if rating <= 3 else [],
            is_verified=True,
            is_public=True,
            helpful_count=random.randint(0, 10),
            not_helpful_count=random.randint(0, 3),
            charging_duration_hours=booking.estimated_duration_minutes / 60,
            energy_charged_kwh=random.uniform(10, 50),
            vehicle_type=booking.vehicle_info.get("type") if booking.vehicle_info else None,
        )
        
        # Add host response occasionally
        if random.choice([True, False]):
            review.host_response = fake.text(max_nb_chars=200)
            review.host_responded_at = str(booking.completed_at + timedelta(days=random.randint(1, 7)))
        
        db.add(review)
    
    db.commit()
    print(f"✅ Created {len(sample_bookings)} reviews")


def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    engine, db = create_engine_and_session()
    
    try:
        # Create admin user
        admin = create_admin_user(db)
        
        # Create test users
        test_host, test_renter = create_test_users(db)
        
        # Create sample users
        users = create_users(db, count=100)
        users.extend([admin, test_host, test_renter])
        
        # Create chargers
        chargers = create_chargers(db, users, count=50)
        
        # Create bookings
        bookings = create_bookings(db, chargers, users, count=200)
        
        # Create reviews
        create_reviews(db, bookings)
        
        print("✅ Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   Users: {len(users)} (including admin and test accounts)")
        print(f"   Chargers: {len(chargers)}")
        print(f"   Bookings: {len(bookings)}")
        print(f"   Cities covered: {len(INDIAN_CITIES)}")
        
        print("\n🔐 Test Credentials:")
        print(f"   Admin: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")
        print(f"   Host: {settings.TEST_HOST_EMAIL} / {settings.TEST_HOST_PASSWORD}")
        print(f"   Renter: {settings.TEST_RENTER_EMAIL} / {settings.TEST_RENTER_PASSWORD}")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()