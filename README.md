AI Research Agent

A full-stack AI-powered research assistant that automatically finds, analyzes, and summarizes the most relevant sources for any topic.

Features
Search any topic (AI, finance, science, etc.)
Returns top 5 strongest sources
AI-generated analysis for each source
Key insights, trends, and applications
Saved reports dashboard
Daily automated research (scheduler)
Clean modern UI (React + Tailwind)
How It Works
User inputs a topic
Backend queries search engine for recent results
Top sources are selected and structured
OpenAI analyzes and synthesizes:
Source breakdown
Trends
Insights
Results are displayed in UI and saved to database
Tech Stack
Frontend
React (Vite)
TailwindCSS
Axios
Backend
FastAPI
OpenAI API
APScheduler
SQLite
 Setup Instructions
1. Clone Repo
git clone https://github.com/yourusername/research-agent.git
cd research-agent
2. Backend Setup
cd backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

Create .env:

OPENAI_API_KEY=your_key_here

Run server:

uvicorn main:app --reload

Backend runs on:

http://localhost:8000
3. Frontend Setup
cd frontend

npm install
npm run dev

Frontend runs on:

http://localhost:5173
 API Endpoints
Run Agent
GET /run/{topic}
Get Saved Reports
GET /reports
 Example

Input:

AI agents 2025

Output:

Top sources with explanations
Key insights
Trends
Applications
 Future Improvements
Source ranking algorithm
Real-time notifications
Cloud deployment (AWS)
User authentication
Trend tracking dashboard
 Author

Shaquille Taj
Queens College – Computer Science
Full-stack + AI Developer

 If you like this project

Give it a star and feel free to fork!