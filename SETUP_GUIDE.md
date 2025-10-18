# 🚀 MCA Insights Engine - Portable Setup Guide

## 📦 **Quick Start (For Anyone)**

### **Windows Users:**
1. **Extract the ZIP file** to any folder
2. **Double-click `run.bat`** 
3. **Wait for setup to complete** (first time only)
4. **Open browser** and go to `http://localhost:5000`

### **Mac/Linux Users:**
1. **Extract the ZIP file** to any folder
2. **Open Terminal** in that folder
3. **Run**: `chmod +x run.sh && ./run.sh`
4. **Open browser** and go to `http://localhost:5000`

---

## 🔧 **What Happens During Setup:**

### **Automatic Setup Process:**
1. ✅ **Checks Python Installation** (requires Python 3.11+)
2. ✅ **Installs Dependencies** (from requirements.txt)
3. ✅ **Sets Up Database** (PostgreSQL with sample data)
4. ✅ **Populates Data** (100 companies from 5 states)
5. ✅ **Starts Application** (Flask server on port 5000)

### **First Time Setup:**
- **Duration**: 2-3 minutes
- **Internet Required**: Yes (for package installation)
- **Database**: Automatically created locally

---

## 📋 **System Requirements:**

### **Minimum Requirements:**
- **Python 3.11+** (download from python.org)
- **4GB RAM** (recommended)
- **1GB Free Disk Space**
- **Internet Connection** (for first-time setup)

### **Supported Operating Systems:**
- ✅ **Windows 10/11**
- ✅ **macOS 10.15+**
- ✅ **Linux (Ubuntu, CentOS, etc.)**

---

## 🎯 **Features Included:**

### **📊 Dashboard:**
- Real-time company statistics
- Interactive charts and visualizations
- State-wise and status-wise distribution

### **🔍 Search & Filter:**
- Multi-criteria company search
- Advanced filtering options
- Export capabilities

### **📈 Change Analysis:**
- Automated change detection
- Historical change tracking
- Detailed change logs

### **🎯 Data Enrichment:**
- Enhanced company data
- Sector classification
- Director information

### **🤖 AI Assistant:**
- OpenAI-powered chatbot
- Natural language queries
- Intelligent responses

### **🔌 REST API:**
- Complete API endpoints
- External integration support
- Data export capabilities

---

## 🛠️ **Manual Setup (If Needed):**

### **Step 1: Install Python**
- Download from: https://python.org
- Make sure to check "Add to PATH" during installation

### **Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 3: Setup Database**
```bash
python data_integration.py
```

### **Step 4: Populate Data**
```bash
python mca_data_processor.py
```

### **Step 5: Run Application**
```bash
python flask_dashboard.py
```

---

## 🔍 **Troubleshooting:**

### **Common Issues:**

1. **"Python not found"**
   - Install Python from python.org
   - Make sure Python is added to PATH

2. **"Permission denied" (Mac/Linux)**
   - Run: `chmod +x run.sh`
   - Or use: `bash run.sh`

3. **"Port 5000 already in use"**
   - Close other applications using port 5000
   - Or change port in flask_dashboard.py

4. **"Database connection failed"**
   - Make sure PostgreSQL is installed
   - Check if port 5432 is available

### **Getting Help:**
- Check the logs in `logs/` folder
- Review error messages in terminal
- Ensure all requirements are met

---

## 📁 **File Structure:**

```
MCA-Insights-Engine/
├── run.bat                 # Windows quick start
├── run.sh                  # Mac/Linux quick start
├── flask_dashboard.py      # Main application
├── requirements.txt        # Python dependencies
├── data_integration.py     # Database setup
├── mca_data_processor.py   # Data population
├── templates/              # Web interface
├── static/                 # CSS and JavaScript
├── data/                   # Sample data files
└── logs/                   # Application logs
```

---

## 🎉 **What You Get:**

### **Sample Data:**
- **100 Companies** from 5 states
- **Complete Change Tracking**
- **Enriched Data** with sectors and directors
- **Working AI Chatbot**

### **Ready-to-Use Features:**
- Professional dashboard
- Advanced search capabilities
- Change analysis tools
- Data enrichment system
- REST API endpoints

---

## 🚀 **Next Steps:**

1. **Run the Application**: Use `run.bat` (Windows) or `run.sh` (Mac/Linux)
2. **Access Dashboard**: Open `http://localhost:5000`
3. **Explore Features**: Try search, change analysis, and AI chatbot
4. **Customize**: Modify data or add new features as needed

---

## 📞 **Support:**

If you encounter any issues:
1. Check this guide first
2. Review error messages
3. Ensure system requirements are met
4. Check logs in `logs/` folder

**Your MCA Insights Engine is ready to use!** 🎯
