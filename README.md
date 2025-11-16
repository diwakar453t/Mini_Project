# ChargeMitra - EV Charger Sharing Platform

A comprehensive peer-to-peer EV charger sharing platform built for India, enabling hosts to monetize their chargers and EV drivers to find convenient charging solutions.

## 🚗 Features

### For EV Drivers (Renters)
- **Smart Search**: Find chargers by location, connector type, power rating, and availability
- **Real-time Booking**: Instant or host-approved bookings with live availability
- **Integrated Payments**: Razorpay + UPI deep links + Stripe fallback
- **Live Sessions**: Track charging progress with real-time telemetry
- **Reviews & Ratings**: Rate hosts and chargers

### For Charger Owners (Hosts)
- **Easy Listing**: Add chargers with photos, specs, and pricing
- **Flexible Pricing**: Per-hour or per-kWh pricing models
- **Availability Management**: Set schedules and block times
- **Earnings Dashboard**: Track revenue and payout requests
- **KYC Verification**: Trusted host badges

### For Administrators
- **User Management**: Manage users, hosts, and listings
- **Dispute Resolution**: Handle booking conflicts and issues
- **Analytics**: Platform metrics and business intelligence
- **Content Moderation**: Review and approve listings

## 🛠️ Tech Stack

### Frontend
- **React 18** with TypeScript and Vite
- **React Router** for navigation
- **TailwindCSS** for styling
- **Framer Motion** for animations
- **shadcn/ui** for accessible components
- **PWA** ready with offline support

### Backend
- **FastAPI** with async/await
- **SQLAlchemy** ORM with Alembic migrations
- **PostgreSQL** database with PostGIS
- **JWT** authentication with role-based access
- **WebSocket** for real-time updates
- **Redis** for caching and sessions

### Payments & Integration
- **Razorpay** (primary) with UPI deep links
- **Stripe** (international fallback)
- **Google Maps** API for geocoding and routing
- **SendGrid** for email notifications
- **Web Push** for notifications

### DevOps
- **Docker** and Docker Compose
- **GitHub Actions** CI/CD
- **AWS ECS** / DigitalOcean deployment ready
- **Terraform** infrastructure templates

## 🚀 Quick Start

> macOS note: This repo uses PostGIS for geo-queries. On your Mac, we’ve configured migrations to skip enabling PostGIS if the extension files aren’t installed yet. For full geo features (map radius search), install PostGIS (see OS-specific setup below).

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ and Python 3.11+
- PostgreSQL 14+ (or use Docker)

### Environment Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd chargemitra
cp .env.example .env
# Edit .env with your API keys and database credentials
```

2. **Required API Keys**:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chargemitra
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Payments
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Maps & Geocoding
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Notifications
SENDGRID_API_KEY=your_sendgrid_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# File Storage (Development)
UPLOAD_PATH=./uploads
# Production S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=ap-south-1

# Environment
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

### Development Setup

1. **Start with Docker Compose**:
```bash
make dev
# Or manually:
docker-compose up -d
```

2. **Initialize Database**:
```bash
make init-db
# Or manually:
docker-compose exec backend alembic upgrade head
```

3. **Seed Sample Data**:
```bash
make seed
# Creates 10 hosts, 50 chargers, 200 bookings, 100 users across Indian cities
```

4. **Run Tests**:
```bash
make test
# Runs both backend (pytest) and frontend (Cypress) tests
```

### Manual Setup (without Docker)

#### macOS (Apple Silicon) Setup
1) Install prerequisites
```bash
# PostgreSQL 14+ (already installed on your Mac) and Redis
brew install redis
brew services start redis

# Optional but recommended for full geo features
brew install postgis
# After install finishes, enable the extension in your DB
createdb chargemitra || true
psql -d chargemitra -c "CREATE EXTENSION IF NOT EXISTS postgis;" || true
```

2) Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt || true
# If network or resolver issues occur, install the essentials:
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary asyncpg pydantic pydantic-settings python-dotenv redis python-multipart geoalchemy2 shapely email-validator passlib[bcrypt] python-jose[cryptography]

# Configure DB URL for your local user (adjust if needed)
# Edit backend/alembic.ini sqlalchemy.url or set env DATABASE_URL:
# export DATABASE_URL=postgresql://<your-user>@localhost:5432/chargemitra

# Create role/db if needed (replace <your-user> with your mac username):
psql -d postgres -c "CREATE USER chargemitra WITH PASSWORD 'chargemitra123';" || true
psql -d postgres -c "CREATE DATABASE chargemitra OWNER chargemitra;" || true

# Run migrations (PostGIS columns require the extension; if missing, migrations will skip enabling it,
# but geo types may still fail. Ensure PostGIS is installed to avoid errors.)
alembic upgrade head

# Seed data (optional)
python scripts/seed_data.py

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3) Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

4) Access
- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (Docs: /docs)

Troubleshooting (macOS)
- PostGIS missing control file: run `brew install postgis` and retry `psql -d chargemitra -c "CREATE EXTENSION postgis;"`
- Redis not found: `brew install redis && brew services start redis`
- Psycopg errors due to role: create role/db as above

#### Windows Setup
1) Install prerequisites
- PostgreSQL 15+ with Stack Builder (install PostGIS extension during setup)
- Redis for Windows (Memurai/Redis on WSL, or Docker)
- Python 3.11+, Node 18+

2) Backend (PowerShell)
```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Set DB URL if needed:
# setx DATABASE_URL "postgresql://postgres:<password>@localhost:5432/chargemitra"

alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3) Frontend (PowerShell)
```powershell
cd frontend
npm install
npm run dev
```

If PostGIS isn’t installed on Windows, use Stack Builder to add it, then run:
```powershell
psql -d chargemitra -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

1. **Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
alembic upgrade head
python scripts/seed_data.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Frontend Setup**:
```bash
cd frontend
npm install
npm run dev
```

## 🗄️ Database Schema

### Core Tables
- **users**: User accounts with KYC status
- **profiles**: Extended user profiles
- **chargers**: Charger listings with geo-location
- **charger_pricing**: Flexible pricing models
- **bookings**: Reservation management
- **sessions**: Actual charging sessions with telemetry
- **reviews**: Ratings and feedback
- **payouts**: Host earnings and transfers
- **disputes**: Conflict resolution
- **audit_logs**: System audit trail

### Key Features
- PostGIS geo-spatial indexing for efficient radius searches
- Atomic booking constraints preventing double-booking
- Comprehensive audit logging for compliance
- Flexible pricing models (per-hour/per-kWh)

## 🔗 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints
- `POST /auth/register` - User registration
- `GET /chargers` - Search chargers with geo-filters
- `POST /bookings` - Create new booking
- `WS /ws/chargers/{charger_id}` - Real-time charger updates
- `POST /payments/create` - Initialize payment

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest -v
# Specific test categories:
pytest tests/test_auth.py -v
pytest tests/test_bookings.py -v
pytest tests/test_payments.py -v
```

### Frontend E2E Tests
```bash
cd frontend
npm run test:e2e
# Or with UI:
npm run cypress:open
```

### Load Testing
```bash
cd tests/load
k6 run booking_flow.js
```

## 🏗️ Project Structure

```
chargemitra/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── api/
│   │   ├── services/
│   │   └── utils/
│   ├── alembic/
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── utils/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── scripts/
├── docs/
└── terraform/
```

## 🚀 Deployment

### Production Deployment

1. **Build Images**:
```bash
make build
docker-compose -f docker-compose.prod.yml build
```

2. **Deploy to AWS ECS**:
```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

3. **Deploy to DigitalOcean**:
```bash
cd scripts
./deploy_digitalocean.sh
```

### Environment Variables for Production
- Set all required API keys
- Use managed database (AWS RDS/DigitalOcean Managed DB)
- Configure S3 for file storage
- Set up SSL certificates
- Configure Redis cluster

## 🔐 Security Features

- JWT authentication with refresh tokens
- Role-based access control (Guest/Renter/Host/Admin)
- Rate limiting on all endpoints
- Input validation and sanitization
- CORS protection
- CSRF tokens for forms
- Encryption at rest for sensitive data
- PCI-compliant payment handling

## 💰 Payment Configuration

### Razorpay Setup (Primary - India)
1. Create account at [razorpay.com](https://razorpay.com)
2. Get API keys from Dashboard
3. Configure webhook endpoint: `https://yourdomain.com/api/payments/webhook`
4. Set webhook secret in environment variables

### UPI Deep Links
- Google Pay: `tez://upi/pay?pa=merchant@paytm&pn=ChargeMitra&am=100`
- PhonePe: `phonepe://pay?pa=merchant@paytm&pn=ChargeMitra&am=100`

### Stripe (International)
1. Create account at [stripe.com](https://stripe.com)
2. Get API keys for your region
3. Configure webhook for payment events

## 📱 Mobile Features

- **Progressive Web App** (PWA) with offline support
- **Push Notifications** for booking updates
- **Mobile Gestures**: Swipe actions, pull-to-refresh
- **Native-like UI** with bottom sheet modals
- **Responsive Design** mobile-first approach

## 🌍 Indian Localization

- **Currency**: INR (₹) formatting
- **Time**: 24-hour IST timezone
- **Language**: Indian English with local terminology
- **Cities**: Pre-seeded with major Indian metros
- **Design**: Warm color palette with Indian aesthetics
- **Compliance**: GST-ready invoicing structure

## 🎨 UI/UX Features

- **Smooth Animations**: Framer Motion micro-interactions
- **Accessibility**: WCAG 2.1 AA compliance
- **Dark Mode**: System preference detection
- **Offline Support**: Last search cache and booking viewing
- **Indian Design**: Subtle traditional motifs and color scheme

## 📊 Analytics & Monitoring

- **Business Metrics**: Host earnings, booking volume, utilization rates
- **Technical Monitoring**: API performance, error rates, uptime
- **User Analytics**: Search patterns, conversion funnels
- **Real-time Dashboards**: Grafana + Prometheus integration

## 🆘 Support & Troubleshooting

### Common Issues
1. **Database Connection**: Check PostgreSQL is running and credentials are correct
2. **API Keys**: Verify all required environment variables are set
3. **WebSocket Issues**: Ensure Redis is running for session management
4. **Payment Failures**: Check Razorpay webhook configuration

### Test Accounts (Development)
```
Admin: admin@chargemitra.com / admin123
Host: host@example.com / host123
Renter: renter@example.com / renter123
```

### Sample Test Cards (Razorpay)
- Success: 4111 1111 1111 1111
- Failure: 4111 1111 1111 1112

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Team**: Built with ❤️ for India's EV ecosystem
- **Inspiration**: Supporting India's transition to electric mobility
- **Community**: Thanks to all contributors and early adopters

---

## 🎯 Implementation Status

### ✅ **Completed Features**

#### **Priority 1: Google Maps Integration (Search Page)**
- **Complete map/list sync** with animated markers and clustering
- **Geocoding and radius search** with fallback to sample data when API key is missing
- **Animated pins** with availability badges that pulse for in-use chargers
- **Real-time map/list synchronization** - scrolling list highlights markers, clicking markers scrolls list into view
- **Advanced filtering** with connector type, charger type, availability, rating, and amenities
- **Responsive design** with mobile/desktop view toggles

#### **Priority 2: Complete Booking Flow**
- **Atomic booking creation** with database constraints and transaction retry logic
- **Time slot picker** with availability checks and price estimation
- **Price calculator** supporting per-hour and per-kWh pricing with platform fees
- **Booking confirmation** with QR codes and access information
- **Overstay handling** with auto-extend logic and fee calculation
- **Conflict prevention** using SELECT FOR UPDATE and database constraints

#### **Priority 3: Dummy Payment System**
- **Complete payment simulation** with developer controls and network delay simulation
- **Multiple payment methods**: UPI, Cards, Digital Wallets with test credentials
- **Animated payment flow** with success confetti and failure handling
- **Developer switches** for simulating failures, latency, and webhook delays
- **Backend integration** with atomic payment completion and booking status updates
- **Mobile-optimized** payment interface with gesture support

#### **Priority 4: WebSocket Real-time Updates**
- **Live telemetry streaming** for charger status, power output, and session progress
- **Automatic reconnection** with exponential backoff and error handling
- **Real-time charger status** with animated availability badges
- **Session progress tracking** with live power, energy, and duration updates
- **Connection status indicators** with online/offline states

#### **Priority 5: Enhanced Telemetry Simulation**
- **Realistic EV charging curves** with constant power and taper phases
- **Multiple charging profiles**: Slow AC, Fast AC, DC Fast, Ultra Fast
- **Environmental factors**: Temperature effects, heat buildup over time
- **Random session management** with automatic start/stop based on usage patterns
- **Manual control interface** for testing different scenarios
- **Redis pub/sub integration** for real-time data distribution

### 🏗️ **Technical Implementation Highlights**

#### **Database & Backend**
- **Atomic booking service** with race condition prevention
- **PostGIS spatial indexing** for efficient geo-queries
- **Comprehensive audit logging** for all critical operations
- **Role-based access control** with JWT authentication
- **Input validation** and SQL injection prevention
- **Database constraints** for business rule enforcement

#### **Frontend Architecture**
- **TypeScript throughout** with comprehensive type definitions
- **Custom hooks** for WebSocket management and API integration
- **Framer Motion animations** with reduced motion support
- **Progressive Web App** (PWA) with offline capabilities
- **Mobile-first responsive design** with gesture support
- **Atomic design system** with reusable components

#### **Real-time Features**
- **WebSocket connection management** with automatic reconnection
- **Live telemetry dashboard** with animated metrics
- **Real-time availability updates** with visual indicators
- **Session progress tracking** with charging curves
- **Push notifications** ready for booking updates

#### **Payment Integration**
- **Razorpay primary** with UPI deep links for India
- **Stripe fallback** for international users
- **Dummy payment system** for development and testing
- **Split payment logic** with platform commission handling
- **Refund management** with partial and full refund support

#### **Security & Performance**
- **Environment-based configuration** with dummy payments only in development
- **Rate limiting** on all API endpoints
- **CORS protection** with configurable origins
- **SQL injection prevention** with parameterized queries
- **XSS protection** with input sanitization
- **HTTPS-ready** with security headers

### 🚀 **Quick Demo**

1. **Start the platform**:
   ```bash
   make dev
   make init-db
   make seed
   ```

2. **Access the application**:
   - Frontend: http://localhost:5173 
   - Backend API: http://localhost:8000/docs
   - Live telemetry: Starts automatically

3. **Test the complete flow**:
   - Search for chargers on the map
   - Click a charger to view details with live telemetry
   - Book a charging slot with time selection
   - Pay using the dummy payment system
   - View real-time session updates

4. **Developer controls**:
   - Toggle `USE_DUMMY_PAYMENTS=true` in environment
   - Use `/payments/dummy` for testing payment flows
   - Monitor WebSocket connections in browser dev tools
   - Control telemetry simulation manually

### 🎮 **Test Credentials**
```
Admin: admin@chargemitra.com / admin123
Host: host@example.com / host123
Renter: renter@example.com / renter123

Dummy Payment Test Cards:
Success: 4111 1111 1111 1111
Failure: 4000 0000 0000 0002
```

### 📱 **Mobile Features**
- **PWA installation** with native-like experience
- **Offline map caching** with last search results
- **Gesture navigation** with swipe and long-press actions
- **Push notifications** for booking updates
- **Bottom sheet modals** for mobile-optimized interactions

### 🔧 **Development Features**
- **Hot reload** for both frontend and backend
- **Comprehensive logging** with structured JSON logs
- **Error monitoring** ready for Sentry integration
- **Performance monitoring** with Prometheus metrics
- **CI/CD pipeline** with GitHub Actions
- **Docker containerization** for consistent deployments

### 📊 **Analytics & Monitoring**
- **Business metrics**: booking rates, revenue, utilization
- **Technical metrics**: API performance, error rates, uptime
- **Real-time dashboards** with live telemetry data
- **User behavior tracking** with search patterns and conversion

---

**ChargeMitra** - Making EV charging accessible across India 🇮🇳⚡