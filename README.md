# EYTGaming Platform 🎮

A comprehensive web platform for managing local and online gaming leagues, tournaments, esports education, and community engagement.

## 🌟 Features

### Core Modules
- **Tournament Engine**: Single/Double elimination, Swiss, Round-robin, Group Stage + Playoffs with pool standings
- **FGC Game Data**: Character & stage tracking per match (Tekken 8, Guilty Gear Strive, and more)
- **Live Updates**: WebSocket + SSE bracket updates pushed in real time
- **Manual Seeding**: Organizer-controlled participant seeding with drag-and-row reordering
- **Bracket UX**: Seed badges, match cards, player advancing highlights
- **Coaching Platform**: Book coaching sessions with integrated payments
- **Team Management**: Create and manage gaming teams
- **Venue Support**: Local event management with QR check-in
- **User Profiles**: Role-based access (Player, Coach, Organizer, Admin)
- **Notifications**: Email, in-app, and push notifications
- **Analytics**: Performance tracking and leaderboards

### Tech Stack
- **Backend**: Django 5.0 + Python 3.11
- **Frontend**: TailwindCSS + Vanilla JavaScript + HTMX
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis + Celery
- **Authentication**: Django-allauth (Discord, Steam, Google)
- **Payments**: Stripe
- **Real-time**: Django Channels (WebSockets)

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for Tailwind)
- Git

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd eytgaming

# Copy environment file
cp .env.example .env

# Update .env with your credentials

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load sample data
docker-compose exec web python manage.py loaddata fixtures/initial_games.json

# Access the application
# Web: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### Option 2: Manual Setup

```bash
# Clone repository
git clone <repository-url>
cd eytgaming

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Create PostgreSQL database
createdb eytgaming_db

# Update .env with your database credentials

# Run setup script
chmod +x setup.sh
./setup.sh

# Start development servers (in separate terminals)
# Terminal 1 - Django
python manage.py runserver

# Terminal 2 - Tailwind CSS
python manage.py tailwind start

# Terminal 3 - Celery Worker
celery -A config worker -l info

# Terminal 4 - Celery Beat
celery -A config beat -l info
```

## 📁 Project Structure

```
eytgaming/
├── config/                 # Django settings & main config
├── core/                   # Custom user model, utilities
├── accounts/              # User profiles & authentication
├── tournaments/           # Tournament & bracket management
├── teams/                 # Team management
├── coaching/              # Coaching/tutoring system
├── venues/                # Venue management
├── payments/              # Payment processing
├── notifications/         # Notification system
├── dashboard/             # User & admin dashboards
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
├── media/                 # User-uploaded files
├── fixtures/              # Initial data
└── tests/                 # Test suites
```

## 🔧 Configuration

### Environment Variables

Key variables to configure in `.env`:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=eytgaming_db
DB_USER=postgres
DB_PASSWORD=your_password

# Social Auth
DISCORD_CLIENT_ID=your_discord_id
DISCORD_CLIENT_SECRET=your_discord_secret
STEAM_API_KEY=your_steam_key
GOOGLE_CLIENT_ID=your_google_id
GOOGLE_CLIENT_SECRET=your_google_secret

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Social Authentication Setup

1. **Discord OAuth**: https://discord.com/developers/applications
2. **Steam OpenID**: https://steamcommunity.com/dev/apikey
3. **Google OAuth**: https://console.cloud.google.com/

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific app tests
pytest tournaments/tests/
```

## 📚 API Documentation

API endpoints will be available at `/api/` (coming soon with DRF integration)

## 🔐 User Roles

| Role | Permissions |
|------|-------------|
| **Guest** | View public tournaments and tutor directory |
| **Player** | Register for tournaments, join teams, book coaching |
| **Coach** | Manage availability, accept bookings, access student notes |
| **Organizer** | Create and manage tournaments |
| **Admin** | Full system access |
| **Parent** | View child's activity and bookings |

## 🎯 Development Roadmap

### Phase 1 - Foundation ✅
- [x] Project setup
- [x] User authentication & profiles
- [x] Core models

### Phase 2 - Tournament Engine ✅
- [x] Bracket generation (single/double elim, Swiss, RR, group stage)
- [x] Match reporting with FGC character/stage selection
- [x] Live bracket updates via WebSocket/SSE
- [x] Check-in system
- [x] Manual seeding with drag-and-drop
- [x] Pool standings with "Advance to Playoffs" button
- [x] Bracket UX with seed badges and match cards

### Phase 3 - Coaching System (In Progress)
- [ ] Tutor profiles & calendar
- [x] Booking system
- [x] Payment integration
- [x] Video call integration

### Phase 4 - Polish & Features
- [ ] Team system
- [x] Venue management
- [ ] Mobile app (React Native)
- [ ] Advanced analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is proprietary. All rights reserved.

## 👥 Team

- **Developer**: [Your Name]
- **Organization**: EYTGaming

## 📁 Archived Docs

Historical implementation reports and task-completion notes have been moved to `docs/_archive/`.

## 📞 Support

- Email: support@eytgaming.com
- Documentation: [Coming Soon]
- Discord: [Coming Soon]

## 🙏 Acknowledgments

- Django community
- TailwindCSS team
- All open-source contributors

---

Made with ❤️ for the esports community