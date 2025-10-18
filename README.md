# 🏢 MCA Insights Engine

**Advanced Corporate Data Analytics Platform**

A comprehensive web application for analyzing MCA (Ministry of Corporate Affairs) data with AI-powered insights, automated change detection, and data enrichment capabilities.

## 🌟 Features

### 📊 **Dashboard Analytics**
- Real-time company statistics and metrics
- Interactive charts and visualizations
- State-wise and status-wise company distribution
- Recent changes tracking

### 🔍 **Advanced Search**
- Multi-criteria company search
- Filter by state, status, year, and keywords
- Detailed company information display
- Export capabilities

### 📈 **Change Analysis**
- Automated change detection
- Historical change tracking
- Change impact analysis
- Detailed change logs

### 🎯 **Data Enrichment**
- Automated data enhancement
- Sector and industry classification
- Director information enrichment
- Website and contact details

### 🤖 **AI-Powered Insights**
- Intelligent chatbot assistant
- Automated report generation
- Data analysis and recommendations
- Natural language queries

### 🔌 **REST API**
- Complete API endpoints
- External integration support
- Data export capabilities
- Third-party application support

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- OpenAI API Key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Raghuchandra-RCP/MCA-Insights-Engine.git
   cd MCA-Insights-Engine
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file:
   ```bash
   # Database Configuration
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=mca_insights_engine
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_postgres_password_here

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here

   # Flask Configuration
   FLASK_ENV=production
   SECRET_KEY=your_secret_key_here
   ```

5. **Initialize database**
   ```bash
   python data_integration.py
   ```

6. **Populate with sample data**
   ```bash
   python mca_data_processor.py
   ```

7. **Run the application**
   ```bash
   python flask_dashboard.py
   ```

8. **Access the application**
   Open your browser and go to `http://localhost:5000`

## 📁 Project Structure

```
MCA-Insights-Engine/
├── flask_dashboard.py          # Main Flask application
├── ai_insights.py              # AI-powered insights engine
├── data_integration.py         # Database integration
├── change_detection.py         # Change detection logic
├── cin_enrichment.py           # Data enrichment system
├── api_server.py               # REST API endpoints
├── mca_data_processor.py       # Data processing pipeline
├── postgresql_config.py        # Database configuration
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── search.html
│   ├── changes.html
│   ├── enrichment.html
│   └── reports.html
├── static/                     # Static assets
│   ├── css/style.css
│   └── js/main.js
├── data/                       # Data files
│   ├── raw/                    # Raw data files
│   ├── processed/              # Processed data
│   ├── enriched/               # Enriched data
│   ├── snapshots/              # Data snapshots
│   └── change_logs/            # Change logs
└── reports/                    # Generated reports
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_HOST` | PostgreSQL host | Yes |
| `POSTGRES_PORT` | PostgreSQL port | Yes |
| `POSTGRES_DB` | Database name | Yes |
| `POSTGRES_USER` | Database user | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `FLASK_ENV` | Flask environment | No |
| `SECRET_KEY` | Flask secret key | Yes |

### Database Schema

The application uses the following main tables:
- `companies` - Company basic information
- `enriched_data` - Enhanced company data
- `change_logs` - Change tracking data
- `data_snapshots` - Historical data snapshots

## 🌐 API Endpoints

### Company Search
- `GET /api/search_company` - Search companies
- `GET /api/company_details/<cin>` - Get company details
- `GET /api/companies_by_state/<state>` - Get companies by state

### Analytics
- `GET /api/dashboard_stats` - Dashboard statistics
- `GET /api/state_distribution` - State-wise distribution
- `GET /api/status_distribution` - Status-wise distribution

### Data Management
- `POST /api/enrich_company` - Enrich company data
- `GET /api/recent_changes` - Get recent changes
- `POST /api/process_data` - Process new data

## 🚀 Deployment

### Production Deployment

The application is production-ready with:
- Security hardening
- Input validation
- SQL injection prevention
- Rate limiting
- Comprehensive logging
- Error handling

### Cloud Deployment Options

1. **Railway** (Recommended)
   - Automatic PostgreSQL database
   - Simple deployment process
   - Built-in CI/CD

2. **Heroku**
   - Popular platform
   - Easy scaling
   - Add-on ecosystem

3. **Render**
   - Modern platform
   - Automatic deployments
   - Built-in monitoring

4. **Docker**
   - Container deployment
   - Multi-platform support
   - Easy scaling

See `DEPLOYMENT.md` for detailed deployment instructions.

## 📊 Features Overview

### Dashboard
- **Total Companies**: Complete count of registered companies
- **Active Companies**: Currently operational companies
- **Recent Changes**: Changes in the last 7 days
- **Enriched Companies**: Companies with additional data
- **State Coverage**: Number of states in database

### Search & Filter
- **Multi-criteria Search**: Search by name, CIN, state, status
- **Advanced Filters**: Filter by multiple criteria
- **Export Options**: Export search results
- **Detailed Views**: Comprehensive company information

### Change Analysis
- **Automated Detection**: Automatic change identification
- **Historical Tracking**: Complete change history
- **Impact Analysis**: Change impact assessment
- **Detailed Logs**: Comprehensive change documentation

### Data Enrichment
- **Sector Classification**: Industry categorization
- **Director Information**: Board member details
- **Contact Enhancement**: Website and contact details
- **Data Validation**: Quality assurance

### AI Assistant
- **Natural Language**: Conversational interface
- **Intelligent Queries**: Context-aware responses
- **Report Generation**: Automated insights
- **Data Analysis**: AI-powered recommendations

## 🔒 Security Features

- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: API protection
- **Security Headers**: HTTP security headers
- **Environment Variables**: Secure configuration
- **Error Handling**: Secure error management

## 📈 Performance

- **Optimized Queries**: Efficient database operations
- **Caching**: Intelligent data caching
- **Pagination**: Large dataset handling
- **Async Processing**: Background task processing
- **Monitoring**: Performance tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## 🎯 Roadmap

- [ ] Real-time notifications
- [ ] Advanced analytics
- [ ] Machine learning models
- [ ] Mobile application
- [ ] API rate limiting
- [ ] Data visualization enhancements

---

**Built with ❤️ for comprehensive corporate data analysis**
