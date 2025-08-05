# AEO Booster

AEO Booster helps optimize your website for AI Engine Optimization (AEO) - ensuring your business appears prominently in AI chatbot recommendations.

## Project Structure

```
aeobooster/
├── src/
│   ├── components/          # React components
│   │   ├── InputForm.jsx   # URL input form
│   │   └── __tests__/      # Component tests
│   ├── api/                # FastAPI endpoints
│   │   └── projects.py     # Project management API
│   └── models/             # Database models
│       ├── database.py     # Database configuration
│       └── project.py      # User and Project models
├── tests/                  # Backend tests
├── public/                 # React public files
├── main.py                # FastAPI application entry point
└── package.json           # React dependencies
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aeobooster
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Development

1. **Start the backend server**
   ```bash
   python start_backend.py
   ```
   The API will be available at http://localhost:8000

2. **Start the frontend development server**
   ```bash
   npm start
   ```
   The React app will be available at http://localhost:3000

### Testing

**Frontend tests (Jest/React Testing Library):**
```bash
npm test
```

**Backend tests (pytest):**
```bash
pytest
```

## API Documentation

When the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /api/projects` - Create a new AEO analysis project
- `GET /api/projects/{project_id}` - Get project details

## Features Implemented

### Story 1.1: URL Input Interface ✅

- ✅ User can enter one or more website URLs in a clear input form
- ✅ System validates that URLs are properly formatted  
- ✅ User receives immediate feedback if a URL is invalid
- ✅ Form is responsive and works on both desktop and mobile devices
- ✅ After submitting URLs, user is taken to the next step in the analysis process

#### Components Created:
- `InputForm.jsx` - Main URL input component with validation
- FastAPI `/api/projects` endpoint for URL submission
- Database models for Users and Projects
- Comprehensive test coverage

## Tech Stack

- **Frontend**: React 18, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy  
- **Database**: SQLite (development), PostgreSQL (production)
- **Testing**: Jest, React Testing Library, pytest
- **Authentication**: Ready for Clerk or Supabase integration

## Contributing

1. Follow the existing code structure and naming conventions
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting PRs