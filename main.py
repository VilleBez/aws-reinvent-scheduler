#!/usr/bin/env python3
"""
AWS re:Invent 2025 Session Scheduler
Main execution script
"""

import argparse
import json
import os
import sys
from datetime import datetime

from config import Config
from scraper.session_scraper import SessionScraper
from processor.keyword_filter import KeywordFilter
from processor.venue_filter import VenueFilter
from processor.session_scorer import SessionScorer
from scheduler.scheduling_algorithm import SchedulingAlgorithm
from output.schedule_formatter import ScheduleFormatter
from output.report_generator import ReportGenerator


def setup_directories():
    """Create necessary directories"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    os.makedirs('logs', exist_ok=True)


def collect_sessions():
    """Collect session data from AWS re:Invent site"""
    print("🔍 Starting session data collection...")
    
    scraper = SessionScraper()
    try:
        sessions = scraper.scrape_all_sessions()
        
        # Save raw data
        raw_file = os.path.join(Config.OUTPUT_DIR, 'raw_sessions.json')
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Collected {len(sessions)} sessions")
        print(f"📁 Raw data saved to: {raw_file}")
        return sessions
        
    except Exception as e:
        print(f"❌ Error collecting sessions: {e}")
        print("💡 Please check your login credentials and network connection")
        raise
    finally:
        scraper.close()


def process_sessions(sessions):
    """Filter and score sessions based on criteria"""
    print("🔄 Processing sessions...")
    
    # Apply keyword filter
    keyword_filter = KeywordFilter(Config.INTEREST_KEYWORDS)
    keyword_filtered = keyword_filter.filter_sessions(sessions)
    print(f"📝 Keyword filter: {len(keyword_filtered)} sessions match interests")
    
    # Apply venue filter
    venue_filter = VenueFilter(Config.EXCLUDED_VENUES)
    venue_filtered = venue_filter.filter_sessions(keyword_filtered)
    print(f"🏢 Venue filter: {len(venue_filtered)} sessions after venue exclusions")
    
    # Score sessions
    scorer = SessionScorer()
    scored_sessions = scorer.score_sessions(venue_filtered)
    
    # Save processed data
    processed_file = os.path.join(Config.OUTPUT_DIR, 'processed_sessions.json')
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(scored_sessions, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Processed data saved to: {processed_file}")
    return scored_sessions


def generate_schedule(sessions):
    """Generate optimized schedule"""
    print("📅 Generating optimized schedule...")
    
    scheduler = SchedulingAlgorithm()
    schedule = scheduler.create_schedule(sessions, Config.CONFERENCE_DATES)
    
    # Save schedule data
    schedule_file = os.path.join(Config.OUTPUT_DIR, 'final_schedule.json')
    with open(schedule_file, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Schedule data saved to: {schedule_file}")
    return schedule


def generate_outputs(schedule, sessions):
    """Generate final output documents"""
    print("📄 Generating output documents...")
    
    # Generate formatted schedule
    formatter = ScheduleFormatter()
    
    if Config.OUTPUT_FORMAT.lower() == 'markdown':
        schedule_md = formatter.to_markdown(schedule)
        md_file = os.path.join(Config.OUTPUT_DIR, 'reinvent_schedule.md')
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(schedule_md)
        print(f"📄 Markdown schedule: {md_file}")
    
    # Generate CSV format as well
    schedule_csv = formatter.to_csv(schedule)
    csv_file = os.path.join(Config.OUTPUT_DIR, 'reinvent_schedule.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(schedule_csv)
    print(f"📊 CSV schedule: {csv_file}")
    
    # Generate detailed report
    report_gen = ReportGenerator()
    report = report_gen.generate_full_report(schedule, sessions)
    
    report_file = os.path.join(Config.OUTPUT_DIR, 'schedule_report.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 Detailed report: {report_file}")


def validate_requirements():
    """Validate that all requirements are met"""
    print("✅ Validating schedule requirements...")
    
    # Check if schedule files exist
    required_files = [
        'final_schedule.json',
        'reinvent_schedule.md',
        'schedule_report.md'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(Config.OUTPUT_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    # Load and validate schedule
    schedule_file = os.path.join(Config.OUTPUT_DIR, 'final_schedule.json')
    try:
        with open(schedule_file, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
        
        # Validate requirements
        validation_results = validate_schedule_requirements(schedule)
        
        print("📋 Requirement Validation Results:")
        for requirement, status in validation_results.items():
            status_icon = "✅" if status['passed'] else "❌"
            print(f"  {status_icon} {requirement}: {status['message']}")
        
        all_passed = all(result['passed'] for result in validation_results.values())
        return all_passed
        
    except Exception as e:
        print(f"❌ Error validating schedule: {e}")
        return False


def validate_schedule_requirements(schedule):
    """Validate specific schedule requirements"""
    results = {}
    
    # 1. Check 30-minute buffer between sessions
    results['30_minute_buffer'] = validate_session_buffers(schedule)
    
    # 2. Check backup sessions (at least 2 per time slot)
    results['backup_sessions'] = validate_backup_sessions(schedule)
    
    # 3. Check lunch break blocking (11:00 AM - 1:00 PM)
    results['lunch_break'] = validate_lunch_breaks(schedule)
    
    # 4. Check venue exclusions (no MGM Grand or Mandalay Bay)
    results['venue_exclusions'] = validate_venue_exclusions(schedule)
    
    # 5. Check keyword coverage
    results['keyword_coverage'] = validate_keyword_coverage(schedule)
    
    return results


def validate_session_buffers(schedule):
    """Validate 30-minute buffers between sessions"""
    conference_dates = [key for key in schedule.keys() if key != 'summary']
    
    for date in conference_dates:
        daily_schedule = schedule[date]
        primary_sessions = daily_schedule.get('primary_sessions', [])
        
        if len(primary_sessions) < 2:
            continue
        
        # Sort by start time
        sorted_sessions = sorted(primary_sessions, key=lambda x: x.get('scheduled_start', '00:00'))
        
        for i in range(len(sorted_sessions) - 1):
            current_end = sorted_sessions[i].get('scheduled_end', '00:00')
            next_start = sorted_sessions[i + 1].get('scheduled_start', '00:00')
            
            try:
                from datetime import datetime
                end_time = datetime.strptime(current_end, '%H:%M')
                start_time = datetime.strptime(next_start, '%H:%M')
                
                gap_minutes = (start_time - end_time).total_seconds() / 60
                
                if gap_minutes < 30:
                    return {
                        'passed': False,
                        'message': f'Insufficient buffer on {date}: {gap_minutes:.0f} minutes'
                    }
            except:
                continue
    
    return {'passed': True, 'message': 'All sessions have adequate 30-minute buffers'}


def validate_backup_sessions(schedule):
    """Validate backup session requirements"""
    conference_dates = [key for key in schedule.keys() if key != 'summary']
    insufficient_slots = []
    
    for date in conference_dates:
        daily_schedule = schedule[date]
        backup_sessions = daily_schedule.get('backup_sessions', {})
        
        for slot_id, backups in backup_sessions.items():
            if len(backups) < Config.MIN_BACKUP_SESSIONS:
                insufficient_slots.append(f"{date}:{slot_id}")
    
    if insufficient_slots:
        return {
            'passed': False,
            'message': f'{len(insufficient_slots)} slots have insufficient backups'
        }
    
    return {'passed': True, 'message': 'All time slots have adequate backup sessions'}


def validate_lunch_breaks(schedule):
    """Validate lunch break blocking"""
    conference_dates = [key for key in schedule.keys() if key != 'summary']
    lunch_conflicts = []
    
    for date in conference_dates:
        daily_schedule = schedule[date]
        primary_sessions = daily_schedule.get('primary_sessions', [])
        
        for session in primary_sessions:
            start_time = session.get('scheduled_start', '00:00')
            end_time = session.get('scheduled_end', '00:00')
            
            try:
                from datetime import datetime
                start = datetime.strptime(start_time, '%H:%M').time()
                end = datetime.strptime(end_time, '%H:%M').time()
                lunch_start = datetime.strptime(Config.LUNCH_BREAK_START, '%H:%M').time()
                lunch_end = datetime.strptime(Config.LUNCH_BREAK_END, '%H:%M').time()
                
                # Check for overlap with lunch break
                if start < lunch_end and end > lunch_start:
                    lunch_conflicts.append(f"{date}: {session.get('title', 'Unknown')[:30]}")
            except:
                continue
    
    if lunch_conflicts:
        return {
            'passed': False,
            'message': f'Lunch break conflicts: {len(lunch_conflicts)} sessions'
        }
    
    return {'passed': True, 'message': 'No sessions scheduled during lunch break'}


def validate_venue_exclusions(schedule):
    """Validate venue exclusions"""
    conference_dates = [key for key in schedule.keys() if key != 'summary']
    excluded_venues_found = []
    
    for date in conference_dates:
        daily_schedule = schedule[date]
        primary_sessions = daily_schedule.get('primary_sessions', [])
        
        for session in primary_sessions:
            venue = session.get('venue', '').lower()
            
            for excluded_venue in Config.EXCLUDED_VENUES:
                if excluded_venue.lower() in venue:
                    excluded_venues_found.append(f"{date}: {venue}")
    
    if excluded_venues_found:
        return {
            'passed': False,
            'message': f'Excluded venues found: {len(excluded_venues_found)} sessions'
        }
    
    return {'passed': True, 'message': 'No sessions at excluded venues (MGM Grand, Mandalay Bay)'}


def validate_keyword_coverage(schedule):
    """Validate keyword coverage"""
    summary = schedule.get('summary', {})
    keyword_coverage = summary.get('overall_keyword_coverage', {})
    
    covered_keywords = set(keyword_coverage.keys())
    target_keywords = set(keyword.lower() for keyword in Config.INTEREST_KEYWORDS)
    
    missing_keywords = target_keywords - covered_keywords
    
    if missing_keywords:
        return {
            'passed': False,
            'message': f'Missing keyword coverage: {", ".join(missing_keywords)}'
        }
    
    return {'passed': True, 'message': 'All target keywords have session coverage'}


def main():
    parser = argparse.ArgumentParser(description='AWS re:Invent 2025 Session Scheduler')
    parser.add_argument('--collect', action='store_true', help='Collect session data')
    parser.add_argument('--process', action='store_true', help='Process collected data')
    parser.add_argument('--schedule', action='store_true', help='Generate schedule')
    parser.add_argument('--output', action='store_true', help='Generate output documents')
    parser.add_argument('--validate', action='store_true', help='Validate requirements')
    parser.add_argument('--all', action='store_true', help='Run complete pipeline')
    
    args = parser.parse_args()
    
    # Validate credentials
    if not Config.REINVENT_EMAIL or not Config.REINVENT_PASSWORD:
        print("❌ Error: Please set REINVENT_EMAIL and REINVENT_PASSWORD in .env file")
        print("💡 Copy .env.example to .env and add your credentials")
        sys.exit(1)
    
    setup_directories()
    
    print("🚀 AWS re:Invent 2025 Session Scheduler")
    print("=" * 50)
    print(f"📧 Email: {Config.REINVENT_EMAIL}")
    print(f"🎯 Keywords: {', '.join(Config.INTEREST_KEYWORDS)}")
    print(f"🚫 Excluded venues: {', '.join(Config.EXCLUDED_VENUES)}")
    print(f"📅 Conference dates: {', '.join(Config.CONFERENCE_DATES)}")
    print("=" * 50)
    
    sessions = None
    processed_sessions = None
    schedule = None
    
    if args.all or args.collect:
        sessions = collect_sessions()
    
    if args.all or args.process:
        if not sessions:
            # Load from file if not collected in this run
            raw_file = os.path.join(Config.OUTPUT_DIR, 'raw_sessions.json')
            if os.path.exists(raw_file):
                with open(raw_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
            else:
                print("❌ No session data found. Run with --collect first.")
                sys.exit(1)
        
        processed_sessions = process_sessions(sessions)
    
    if args.all or args.schedule:
        if not processed_sessions:
            # Load from file if not processed in this run
            processed_file = os.path.join(Config.OUTPUT_DIR, 'processed_sessions.json')
            if os.path.exists(processed_file):
                with open(processed_file, 'r', encoding='utf-8') as f:
                    processed_sessions = json.load(f)
            else:
                print("❌ No processed session data found. Run with --process first.")
                sys.exit(1)
        
        schedule = generate_schedule(processed_sessions)
    
    if args.all or args.output:
        if not schedule:
            # Load from file if not scheduled in this run
            schedule_file = os.path.join(Config.OUTPUT_DIR, 'final_schedule.json')
            if os.path.exists(schedule_file):
                with open(schedule_file, 'r', encoding='utf-8') as f:
                    schedule = json.load(f)
            else:
                print("❌ No schedule data found. Run with --schedule first.")
                sys.exit(1)
        
        if not processed_sessions:
            processed_file = os.path.join(Config.OUTPUT_DIR, 'processed_sessions.json')
            if os.path.exists(processed_file):
                with open(processed_file, 'r', encoding='utf-8') as f:
                    processed_sessions = json.load(f)
        
        generate_outputs(schedule, processed_sessions)
    
    if args.all or args.validate:
        validation_passed = validate_requirements()
        if not validation_passed:
            print("❌ Schedule validation failed!")
            sys.exit(1)
    
    print("\n✅ Pipeline completed successfully!")
    print(f"📁 All outputs saved to: {Config.OUTPUT_DIR}/")
    print("\n📋 Generated files:")
    print(f"  - reinvent_schedule.md (Main schedule)")
    print(f"  - reinvent_schedule.csv (CSV format)")
    print(f"  - schedule_report.md (Detailed analysis)")
    print(f"  - final_schedule.json (Raw data)")


if __name__ == "__main__":
    main()