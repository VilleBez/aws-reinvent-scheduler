"""
Schedule formatter for AWS re:Invent sessions
"""

from typing import Dict, Any, List
from datetime import datetime


class ScheduleFormatter:
    def __init__(self):
        self.date_format = '%Y-%m-%d'
        self.time_format = '%H:%M'
    
    def to_markdown(self, schedule: Dict[str, Any]) -> str:
        """Convert schedule to markdown format"""
        markdown_content = []
        
        # Add title and header
        markdown_content.append("# AWS re:Invent 2025 - Optimized Schedule")
        markdown_content.append("")
        markdown_content.append("Generated schedule based on your interests: AI, Kiro, Architect, Lakehouse, ETL, Trino, DevOps")
        markdown_content.append("")
        
        # Add summary if available
        if 'summary' in schedule:
            markdown_content.extend(self._format_summary(schedule['summary']))
            markdown_content.append("")
        
        # Add daily schedules
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        conference_dates.sort()
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            markdown_content.extend(self._format_daily_schedule(date, daily_schedule))
            markdown_content.append("")
        
        # Add backup sessions section
        markdown_content.extend(self._format_backup_sessions(schedule))
        
        # Add venue information
        markdown_content.extend(self._format_venue_information(schedule))
        
        return "\n".join(markdown_content)
    
    def _format_summary(self, summary: Dict[str, Any]) -> List[str]:
        """Format schedule summary"""
        content = []
        content.append("## 📊 Schedule Summary")
        content.append("")
        
        content.append(f"- **Total Conference Days**: {summary.get('total_conference_days', 0)}")
        content.append(f"- **Total Scheduled Sessions**: {summary.get('total_scheduled_sessions', 0)}")
        content.append(f"- **Total Backup Sessions**: {summary.get('total_backup_sessions', 0)}")
        content.append(f"- **Average Session Score**: {summary.get('average_session_score', 0):.2f}/1.00")
        content.append(f"- **Schedule Efficiency**: {summary.get('schedule_efficiency', 0)} sessions/day")
        content.append("")
        
        # Keyword coverage
        keyword_coverage = summary.get('overall_keyword_coverage', {})
        if keyword_coverage:
            content.append("### 🎯 Keyword Coverage")
            for keyword, count in sorted(keyword_coverage.items(), key=lambda x: x[1], reverse=True):
                content.append(f"- **{keyword}**: {count} sessions")
            content.append("")
        
        # Venue distribution
        venue_dist = summary.get('overall_venue_distribution', {})
        if venue_dist:
            content.append("### 🏢 Venue Distribution")
            for venue, count in sorted(venue_dist.items(), key=lambda x: x[1], reverse=True):
                content.append(f"- **{venue}**: {count} sessions")
            content.append("")
        
        return content
    
    def _format_daily_schedule(self, date: str, daily_schedule: Dict[str, Any]) -> List[str]:
        """Format a single day's schedule"""
        content = []
        
        # Format date header
        try:
            date_obj = datetime.strptime(date, self.date_format)
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            formatted_date = date
        
        content.append(f"## 📅 {formatted_date}")
        content.append("")
        
        # Add daily statistics
        stats = daily_schedule.get('statistics', {})
        content.append(f"**Sessions Scheduled**: {stats.get('scheduled_sessions', 0)} | "
                      f"**Backup Options**: {stats.get('backup_sessions', 0)} | "
                      f"**Average Score**: {stats.get('average_score', 0):.2f}")
        content.append("")
        
        # Add primary sessions table
        primary_sessions = daily_schedule.get('primary_sessions', [])
        if primary_sessions:
            content.append("### 🎯 Primary Schedule")
            content.append("")
            content.append("| Time | Session | Venue | Score | Keywords |")
            content.append("|------|---------|-------|-------|----------|")
            
            for session in sorted(primary_sessions, key=lambda x: x.get('scheduled_start', '00:00')):
                time_range = f"{session.get('scheduled_start', 'TBD')} - {session.get('scheduled_end', 'TBD')}"
                title = session.get('title', 'Unknown Session')[:50]
                if len(session.get('title', '')) > 50:
                    title += "..."
                
                venue = session.get('venue', 'TBD')
                score = f"{session.get('score', 0):.2f}"
                keywords = ", ".join(session.get('keywords_matched', []))[:30]
                if len(", ".join(session.get('keywords_matched', []))) > 30:
                    keywords += "..."
                
                content.append(f"| {time_range} | {title} | {venue} | {score} | {keywords} |")
            
            content.append("")
        
        # Add lunch break notice
        blocked_times = daily_schedule.get('blocked_times', [])
        if blocked_times:
            content.append("### 🍽️ Blocked Times")
            for blocked_time in blocked_times:
                content.append(f"- **{blocked_time}**: Lunch Break")
            content.append("")
        
        # Add session details
        if primary_sessions:
            content.append("### 📝 Session Details")
            content.append("")
            
            for i, session in enumerate(sorted(primary_sessions, key=lambda x: x.get('scheduled_start', '00:00')), 1):
                content.append(f"#### {i}. {session.get('title', 'Unknown Session')}")
                content.append("")
                content.append(f"**Time**: {session.get('scheduled_start', 'TBD')} - {session.get('scheduled_end', 'TBD')}")
                content.append(f"**Venue**: {session.get('venue', 'TBD')}")
                if session.get('room'):
                    content.append(f"**Room**: {session.get('room')}")
                content.append(f"**Score**: {session.get('score', 0):.2f}/1.00")
                
                if session.get('keywords_matched'):
                    content.append(f"**Keywords**: {', '.join(session.get('keywords_matched'))}")
                
                if session.get('level'):
                    content.append(f"**Level**: {session.get('level')}")
                
                if session.get('speakers'):
                    speakers = ', '.join(session.get('speakers'))
                    content.append(f"**Speakers**: {speakers}")
                
                if session.get('description'):
                    desc = session.get('description')[:200]
                    if len(session.get('description', '')) > 200:
                        desc += "..."
                    content.append(f"**Description**: {desc}")
                
                content.append("")
        
        return content
    
    def _format_backup_sessions(self, schedule: Dict[str, Any]) -> List[str]:
        """Format backup sessions section"""
        content = []
        content.append("## 🔄 Backup Sessions")
        content.append("")
        content.append("Alternative sessions for each time slot in case primary sessions are full or cancelled.")
        content.append("")
        
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        conference_dates.sort()
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            backup_sessions = daily_schedule.get('backup_sessions', {})
            
            if not backup_sessions:
                continue
            
            try:
                date_obj = datetime.strptime(date, self.date_format)
                formatted_date = date_obj.strftime('%A, %B %d')
            except:
                formatted_date = date
            
            content.append(f"### {formatted_date}")
            content.append("")
            
            for slot_id, backups in backup_sessions.items():
                if not backups:
                    continue
                
                content.append(f"#### Time Slot: {slot_id}")
                content.append("")
                
                for i, backup in enumerate(backups[:3], 1):  # Show top 3 backups
                    title = backup.get('title', 'Unknown Session')
                    time_range = f"{backup.get('start_time', 'TBD')} - {backup.get('end_time', 'TBD')}"
                    venue = backup.get('venue', 'TBD')
                    score = backup.get('backup_score', backup.get('score', 0))
                    
                    content.append(f"{i}. **{title}**")
                    content.append(f"   - Time: {time_range}")
                    content.append(f"   - Venue: {venue}")
                    content.append(f"   - Score: {score:.2f}")
                    
                    if backup.get('keywords_matched'):
                        content.append(f"   - Keywords: {', '.join(backup.get('keywords_matched'))}")
                    
                    content.append("")
        
        return content
    
    def _format_venue_information(self, schedule: Dict[str, Any]) -> List[str]:
        """Format venue information and travel tips"""
        content = []
        content.append("## 🗺️ Venue Information")
        content.append("")
        
        # Collect all venues from the schedule
        all_venues = set()
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            primary_sessions = daily_schedule.get('primary_sessions', [])
            
            for session in primary_sessions:
                venue = session.get('venue')
                if venue:
                    all_venues.add(venue)
        
        if all_venues:
            content.append("### 📍 Venues in Your Schedule")
            for venue in sorted(all_venues):
                content.append(f"- **{venue}**")
            content.append("")
        
        # Add travel tips
        content.append("### 🚶 Travel Tips")
        content.append("")
        content.append("- **Buffer Time**: 30 minutes between sessions for travel")
        content.append("- **Lunch Break**: 11:00 AM - 1:00 PM daily (no sessions scheduled)")
        content.append("- **Excluded Venues**: MGM Grand and Mandalay Bay (as requested)")
        content.append("- **Recommended**: Download venue maps and plan routes in advance")
        content.append("- **Transportation**: Consider using rideshare or walking between nearby venues")
        content.append("")
        
        # Add schedule notes
        content.append("### 📋 Schedule Notes")
        content.append("")
        content.append("- Sessions are prioritized by relevance to your keywords")
        content.append("- Backup sessions are provided for flexibility")
        content.append("- All times are in conference local time")
        content.append("- Check official AWS re:Invent app for real-time updates")
        content.append("")
        
        return content
    
    def to_csv(self, schedule: Dict[str, Any]) -> str:
        """Convert schedule to CSV format"""
        csv_lines = []
        csv_lines.append("Date,Start Time,End Time,Session Title,Venue,Room,Score,Keywords,Level,Speakers")
        
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        conference_dates.sort()
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            primary_sessions = daily_schedule.get('primary_sessions', [])
            
            for session in sorted(primary_sessions, key=lambda x: x.get('scheduled_start', '00:00')):
                fields = [
                    date,
                    session.get('scheduled_start', ''),
                    session.get('scheduled_end', ''),
                    f'"{session.get("title", "").replace(chr(34), chr(34)+chr(34))}"',
                    session.get('venue', ''),
                    session.get('room', ''),
                    str(session.get('score', 0)),
                    f'"{", ".join(session.get("keywords_matched", []))}"',
                    session.get('level', ''),
                    f'"{", ".join(session.get("speakers", []))}"'
                ]
                csv_lines.append(",".join(fields))
        
        return "\n".join(csv_lines)