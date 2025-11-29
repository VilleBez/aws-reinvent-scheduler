# AWS re:Invent 2025 Session Scheduler

An intelligent session scheduler for AWS re:Invent 2025 that automatically collects, filters, and optimizes your conference schedule based on your interests.

## 🎯 Features

- **Automated Session Collection**: Scrapes all AWS re:Invent 2025 sessions from the official event catalog
- **Smart Filtering**: Filters sessions based on your interest keywords (AI, Kiro, Architect, Lakehouse, ETL, Trino, DevOps)
- **Venue Optimization**: Excludes specified venues (MGM Grand, Mandalay Bay) and optimizes for travel time
- **Intelligent Scheduling**: Creates optimized 5-day schedule with 30-minute buffers between sessions
- **Backup Sessions**: Provides 2+ backup options for each time slot
- **Lunch Break Protection**: Automatically blocks 11:00 AM - 1:00 PM for lunch
- **Multiple Output Formats**: Generates Markdown, CSV, and detailed analysis reports

## 📋 Requirements

- Python 3.8+
- Chrome browser (for web scraping)
- AWS re:Invent registration credentials

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd aws-reinvent-scheduler

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Add your AWS re:Invent registration credentials:
```
REINVENT_EMAIL=your-email@example.com
REINVENT_PASSWORD=your-password
```

### 3. Run the Scheduler

```bash
# Run complete pipeline
python main.py --all

# Or run individual steps
python main.py --collect    # Collect session data
python main.py --process    # Filter and score sessions
python main.py --schedule   # Generate optimized schedule
python main.py --output     # Create formatted outputs
python main.py --validate   # Validate requirements
```

## 📁 Output Files

The scheduler generates several output files in the `data/` directory:

- **`reinvent_schedule.md`** - Main schedule in Markdown format
- **`reinvent_schedule.csv`** - Schedule in CSV format for spreadsheets
- **`schedule_report.md`** - Detailed analysis and recommendations
- **`final_schedule.json`** - Raw schedule data
- **`processed_sessions.json`** - Filtered and scored sessions
- **`raw_sessions.json`** - Original scraped session data

## ⚙️ Configuration Options

Edit `config.py` or use environment variables to customize:

### Interest Keywords
```python
INTEREST_KEYWORDS = [
    'AI', 'Kiro', 'Architect', 'Lakehouse', 
    'ETL', 'Trino', 'DevOps'
]
```

### Excluded Venues
```python
EXCLUDED_VENUES = [
    'MGM Grand',
    'Mandalay Bay'
]
```

### Schedule Settings
```python
LUNCH_BREAK_START = '11:00'
LUNCH_BREAK_END = '13:00'
BUFFER_MINUTES = 30
MIN_BACKUP_SESSIONS = 2
MAX_SESSIONS_PER_DAY = 8
```

## 📊 Schedule Requirements

The scheduler ensures all requirements are met:

✅ **30-minute buffer** between sessions for travel time  
✅ **2+ backup sessions** for each time slot  
✅ **Lunch break protection** (11:00 AM - 1:00 PM blocked)  
✅ **Venue exclusions** (MGM Grand, Mandalay Bay avoided)  
✅ **Keyword relevance** (AI, Kiro, Architect, Lakehouse, ETL, Trino, DevOps)  

## 🏗️ Project Structure

```
aws-reinvent-scheduler/
├── main.py                 # Main execution script
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── scraper/               # Web scraping modules
│   ├── session_scraper.py # Main scraper
│   └── data_parser.py     # Session data parser
├── processor/             # Data processing modules
│   ├── keyword_filter.py  # Keyword filtering
│   ├── venue_filter.py    # Venue filtering
│   └── session_scorer.py  # Session scoring
├── scheduler/             # Scheduling algorithms
│   ├── scheduling_algorithm.py # Main scheduler
│   ├── conflict_resolver.py   # Conflict resolution
│   └── backup_generator.py    # Backup session generator
├── output/                # Output generation
│   ├── schedule_formatter.py  # Format schedules
│   └── report_generator.py    # Generate reports
└── data/                  # Generated data files
```

## 🔧 Advanced Usage

### Custom Keyword Filtering

```bash
# Edit config.py to add custom keywords
INTEREST_KEYWORDS = ['AI', 'Machine Learning', 'Serverless', 'Containers']
```

### Venue Preferences

```bash
# Modify venue scoring in processor/session_scorer.py
venue_convenience_scores = {
    'venetian': 0.9,
    'palazzo': 0.9,
    'wynn': 0.8,
    # Add your preferred venues
}
```

### Schedule Optimization

```bash
# Adjust scheduling parameters in config.py
BUFFER_MINUTES = 45        # Longer travel time
MAX_SESSIONS_PER_DAY = 6   # Fewer sessions per day
```

## 🐛 Troubleshooting

### Common Issues

**Login Failed**
- Verify credentials in `.env` file
- Check if AWS re:Invent site structure changed
- Ensure Chrome browser is installed

**No Sessions Found**
- Check internet connection
- Verify conference dates in `config.py`
- Try running with `--collect` flag separately

**Insufficient Backup Sessions**
- Expand keyword criteria
- Reduce venue exclusions
- Lower `MIN_BACKUP_SESSIONS` requirement

### Debug Mode

```bash
# Run with verbose output
CHROME_HEADLESS=false python main.py --collect
```

## 📈 Performance Tips

- **Parallel Processing**: The scraper uses efficient pagination
- **Caching**: Intermediate results are saved for resuming
- **Rate Limiting**: Respectful delays between requests
- **Memory Management**: Large datasets handled efficiently

## 🔒 Security & Privacy

- **Local Processing**: All data stays on your machine
- **Credential Security**: Uses environment variables
- **No Cloud Upload**: No external data transmission
- **Session Cleanup**: Browser sessions properly closed

## 📝 Example Output

### Schedule Summary
```
📊 Schedule Summary
- Total Conference Days: 5
- Total Scheduled Sessions: 32
- Total Backup Sessions: 96
- Average Session Score: 0.78/1.00
- Schedule Efficiency: 6.4 sessions/day

🎯 Keyword Coverage
- AI: 12 sessions
- Architect: 8 sessions
- DevOps: 7 sessions
- Lakehouse: 5 sessions
```

### Daily Schedule
```
📅 Monday, December 1, 2025

🎯 Primary Schedule
| Time | Session | Venue | Score | Keywords |
|------|---------|-------|-------|----------|
| 09:00 - 10:30 | Building AI-Powered Applications | Venetian | 0.89 | AI, Architect |
| 13:30 - 15:00 | Modern Data Lakehouse Architecture | Palazzo | 0.85 | Lakehouse, Architect |
```

## 🤝 Contributing

This is a specialized tool for AWS re:Invent 2025. For improvements:

1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request

## 📄 License

This project is for personal use at AWS re:Invent 2025. Please respect AWS terms of service and conference policies.

## 🆘 Support

For issues or questions:
1. Check troubleshooting section
2. Review configuration settings
3. Validate input requirements
4. Check AWS re:Invent site status

---

**Happy conferencing! 🎉**

*Generated schedule will help you maximize your AWS re:Invent 2025 experience with optimized session selection and intelligent scheduling.*