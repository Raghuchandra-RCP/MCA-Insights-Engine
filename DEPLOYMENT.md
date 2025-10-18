# 🚀 MCA Insights Engine - Deployment Guide

## 🌐 Cloud Deployment Options

### 1. Railway (Recommended - Easiest)

Railway is the simplest option for deployment with automatic PostgreSQL database.

#### Steps:
1. **Sign up**: Go to [railway.app](https://railway.app) and sign up with GitHub
2. **Connect Repository**: 
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `MCA-Insights-Engine` repository
3. **Add Database**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable
4. **Set Environment Variables**:
   - Go to your service → Variables tab
   - Add these variables:
     ```
     FLASK_ENV=production
     OPENAI_API_KEY=your_openai_api_key_here
     SECRET_KEY=your_secret_key_here
     ```
5. **Deploy**: Railway will automatically deploy your app
6. **Access**: Your app will be available at `https://your-app-name.railway.app`

#### Railway Configuration:
- Uses `railway.json` for configuration
- Automatic PostgreSQL database provisioning
- Built-in CI/CD from GitHub

---

### 2. Heroku

#### Prerequisites:
- Heroku CLI installed
- Heroku account

#### Steps:
1. **Install Heroku CLI**:
   ```bash
   # Windows
   winget install Heroku.HerokuCLI
   
   # Or download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and Create App**:
   ```bash
   heroku login
   heroku create mca-insights-engine
   ```

3. **Add PostgreSQL Database**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set Environment Variables**:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set OPENAI_API_KEY=your_openai_api_key_here
   heroku config:set SECRET_KEY=your_secret_key_here
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

6. **Open App**:
   ```bash
   heroku open
   ```

---

### 3. Render

#### Steps:
1. **Sign up**: Go to [render.com](https://render.com) and sign up
2. **Create New Web Service**:
   - Connect your GitHub repository
   - Select `MCA-Insights-Engine`
3. **Configure Service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 30 flask_dashboard:app`
   - **Environment**: Python 3.11
4. **Add Database**:
   - Create new PostgreSQL database
   - Copy connection string
5. **Set Environment Variables**:
   ```
   FLASK_ENV=production
   DATABASE_URL=your_postgresql_connection_string
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```
6. **Deploy**: Click "Create Web Service"

---

### 4. DigitalOcean App Platform

#### Steps:
1. **Sign up**: Go to [DigitalOcean](https://cloud.digitalocean.com)
2. **Create App**:
   - Connect GitHub repository
   - Select `MCA-Insights-Engine`
3. **Configure**:
   - **Source**: GitHub repository
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 30 flask_dashboard:app`
4. **Add Database**:
   - Add PostgreSQL database component
5. **Environment Variables**:
   ```
   FLASK_ENV=production
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

---

## 🐳 Docker Deployment

### Local Docker:
```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:5000
```

### Docker Hub Deployment:
```bash
# Build image
docker build -t mca-insights-engine .

# Tag for Docker Hub
docker tag mca-insights-engine your-username/mca-insights-engine:latest

# Push to Docker Hub
docker push your-username/mca-insights-engine:latest
```

---

## 🔧 Environment Variables

### Required Variables:
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mca_insights_engine
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Flask
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# Optional
PORT=5000
HOST=0.0.0.0
LOG_LEVEL=INFO
```

### Cloud Platform Specific:
- **Railway**: Uses `DATABASE_URL` automatically
- **Heroku**: Uses `DATABASE_URL` from PostgreSQL addon
- **Render**: Uses `DATABASE_URL` from PostgreSQL service

---

## 📊 Production Checklist

### ✅ Pre-Deployment:
- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] OpenAI API key valid
- [ ] All dependencies in requirements.txt
- [ ] Logging configured
- [ ] Error handling implemented

### ✅ Post-Deployment:
- [ ] Application accessible via URL
- [ ] Database connection working
- [ ] AI chatbot functional
- [ ] All pages loading correctly
- [ ] Search functionality working
- [ ] Reports generating properly

---

## 🔍 Troubleshooting

### Common Issues:

1. **Database Connection Error**:
   - Check `DATABASE_URL` or individual PostgreSQL variables
   - Ensure database is accessible from deployment platform

2. **OpenAI API Error**:
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key has sufficient credits

3. **Build Failures**:
   - Check `requirements.txt` for all dependencies
   - Ensure Python version compatibility

4. **Memory Issues**:
   - Reduce worker count in Gunicorn command
   - Optimize data processing queries

### Logs:
- **Railway**: View logs in dashboard
- **Heroku**: `heroku logs --tail`
- **Render**: View logs in dashboard
- **Docker**: `docker-compose logs -f`

---

## 🚀 Quick Deploy Commands

### Railway (One-click):
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy)

### Heroku:
```bash
git clone https://github.com/Raghuchandra-RCP/MCA-Insights-Engine.git
cd MCA-Insights-Engine
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

### Docker:
```bash
git clone https://github.com/Raghuchandra-RCP/MCA-Insights-Engine.git
cd MCA-Insights-Engine
docker-compose up --build
```

---

## 📈 Monitoring & Maintenance

### Health Checks:
- Application responds to `/` endpoint
- Database queries execute successfully
- AI features functional
- All static assets load

### Performance Monitoring:
- Response times < 2 seconds
- Memory usage < 512MB
- Database query optimization
- Error rate < 1%

### Regular Maintenance:
- Update dependencies monthly
- Monitor OpenAI API usage
- Backup database regularly
- Review and rotate secrets

---

## 🎯 Recommended Deployment: Railway

**Why Railway?**
- ✅ Automatic PostgreSQL database
- ✅ Simple GitHub integration
- ✅ Built-in CI/CD
- ✅ Generous free tier
- ✅ Easy environment variable management
- ✅ Automatic HTTPS
- ✅ Custom domains support

**Next Steps:**
1. Push your code to GitHub
2. Sign up at [railway.app](https://railway.app)
3. Deploy from GitHub repository
4. Add environment variables
5. Your app will be live! 🚀
