"""
Scheduling algorithm for AWS re:Invent sessions
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from config import Config
from .conflict_resolver import ConflictResolver
from .backup_generator import BackupGenerator


class SchedulingAlgorithm:
    def __init__(self):
        self.conflict_resolver = ConflictResolver()
        self.backup_generator = BackupGenerator()
        
        # Time slot configuration
        self.lunch_start = datetime.strptime(Config.LUNCH_BREAK_START, '%H:%M').time()
        self.lunch_end = datetime.strptime(Config.LUNCH_BREAK_END, '%H:%M').time()
        self.buffer_minutes = Config.BUFFER_MINUTES
        self.max_sessions_per_day = Config.MAX_SESSIONS_PER_DAY
    
    def create_schedule(self, sessions: List[Dict[str, Any]], 
                       conference_dates: List[str]) -> Dict[str, Any]:
        """Create optimized schedule for all conference days"""
        print("🗓️ Creating optimized schedule...")
        
        # Group sessions by date
        sessions_by_date = self._group_sessions_by_date(sessions, conference_dates)
        
        schedule = {}
        
        for date in conference_dates:
            print(f"\n📅 Scheduling for {date}...")
            
            daily_sessions = sessions_by_date.get(date, [])
            if not daily_sessions:
                print(f"⚠️ No sessions found for {date}")
                schedule[date] = {
                    'primary_sessions': [],
                    'backup_sessions': [],
                    'blocked_times': [f"{Config.LUNCH_BREAK_START}-{Config.LUNCH_BREAK_END}"],
                    'statistics': {
                        'total_sessions': 0,
                        'scheduled_sessions': 0,
                        'backup_sessions': 0
                    }
                }
                continue
            
            daily_schedule = self._create_daily_schedule(daily_sessions, date)
            schedule[date] = daily_schedule
        
        # Add overall statistics
        schedule['summary'] = self._generate_schedule_summary(schedule)
        
        print(f"\n✅ Schedule created for {len(conference_dates)} days")
        return schedule
    
    def _group_sessions_by_date(self, sessions: List[Dict[str, Any]], 
                               conference_dates: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Group sessions by conference date"""
        sessions_by_date = {date: [] for date in conference_dates}
        
        for session in sessions:
            session_date = session.get('date')
            if session_date in conference_dates:
                sessions_by_date[session_date].append(session)
        
        return sessions_by_date
    
    def _create_daily_schedule(self, sessions: List[Dict[str, Any]], 
                              date: str) -> Dict[str, Any]:
        """Create optimized schedule for a single day"""
        # Sort sessions by score (highest first)
        sorted_sessions = sorted(sessions, key=lambda x: x.get('score', 0), reverse=True)
        
        # Create time slots for the day
        time_slots = self._generate_time_slots(sorted_sessions, date)
        
        # Schedule primary sessions
        primary_sessions = self._schedule_primary_sessions(sorted_sessions, time_slots)
        
        # Generate backup sessions for each time slot
        backup_sessions = self.backup_generator.generate_backups(
            sorted_sessions, primary_sessions, time_slots
        )
        
        # Resolve any conflicts
        resolved_schedule = self.conflict_resolver.resolve_conflicts(
            primary_sessions, backup_sessions, time_slots
        )
        
        # Calculate statistics
        statistics = self._calculate_daily_statistics(
            sessions, resolved_schedule['primary'], resolved_schedule['backups']
        )
        
        return {
            'primary_sessions': resolved_schedule['primary'],
            'backup_sessions': resolved_schedule['backups'],
            'blocked_times': [f"{Config.LUNCH_BREAK_START}-{Config.LUNCH_BREAK_END}"],
            'time_slots': time_slots,
            'statistics': statistics
        }
    
    def _generate_time_slots(self, sessions: List[Dict[str, Any]], 
                            date: str) -> List[Dict[str, Any]]:
        """Generate available time slots for the day"""
        time_slots = []
        
        # Get all session times for this day
        session_times = []
        for session in sessions:
            start_time = session.get('start_time')
            end_time = session.get('end_time')
            if start_time and end_time:
                session_times.append((start_time, end_time))
        
        if not session_times:
            return time_slots
        
        # Sort by start time
        session_times.sort()
        
        # Create time slots based on actual session times
        for i, (start_time, end_time) in enumerate(session_times):
            # Skip lunch time sessions
            if self._is_lunch_time(start_time, end_time):
                continue
            
            # Check if this time slot conflicts with already scheduled slots
            conflicts_with_existing = False
            for existing_slot in time_slots:
                if self._times_overlap(start_time, end_time, 
                                     existing_slot['start_time'], 
                                     existing_slot['end_time']):
                    conflicts_with_existing = True
                    break
            
            if not conflicts_with_existing:
                time_slots.append({
                    'slot_id': f"slot_{len(time_slots) + 1}",
                    'start_time': start_time,
                    'end_time': end_time,
                    'date': date,
                    'is_lunch_break': False,
                    'buffer_before': self.buffer_minutes,
                    'buffer_after': self.buffer_minutes
                })
        
        # Limit to max sessions per day
        time_slots = time_slots[:self.max_sessions_per_day]
        
        return time_slots
    
    def _schedule_primary_sessions(self, sessions: List[Dict[str, Any]], 
                                  time_slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Schedule primary sessions in available time slots"""
        primary_sessions = []
        used_sessions = set()
        
        for slot in time_slots:
            # Find best session for this time slot
            best_session = None
            best_score = -1
            
            for session in sessions:
                session_id = session.get('session_id')
                if session_id in used_sessions:
                    continue
                
                # Check if session time matches slot
                if (session.get('start_time') == slot['start_time'] and 
                    session.get('end_time') == slot['end_time']):
                    
                    score = session.get('score', 0)
                    if score > best_score:
                        best_session = session
                        best_score = score
            
            if best_session:
                scheduled_session = best_session.copy()
                scheduled_session['time_slot'] = slot['slot_id']
                scheduled_session['scheduled_start'] = slot['start_time']
                scheduled_session['scheduled_end'] = slot['end_time']
                
                primary_sessions.append(scheduled_session)
                used_sessions.add(best_session.get('session_id'))
        
        return primary_sessions
    
    def _is_lunch_time(self, start_time: str, end_time: str) -> bool:
        """Check if session overlaps with lunch break"""
        try:
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            
            # Check for overlap with lunch break
            return (start < self.lunch_end and end > self.lunch_start)
        except:
            return False
    
    def _times_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time ranges overlap"""
        try:
            s1 = datetime.strptime(start1, '%H:%M')
            e1 = datetime.strptime(end1, '%H:%M')
            s2 = datetime.strptime(start2, '%H:%M')
            e2 = datetime.strptime(end2, '%H:%M')
            
            return s1 < e2 and s2 < e1
        except:
            return False
    
    def _calculate_daily_statistics(self, all_sessions: List[Dict[str, Any]], 
                                   primary_sessions: List[Dict[str, Any]], 
                                   backup_sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate statistics for daily schedule"""
        total_backups = sum(len(backups) for backups in backup_sessions.values())
        
        # Calculate average score
        primary_scores = [s.get('score', 0) for s in primary_sessions]
        avg_score = sum(primary_scores) / len(primary_scores) if primary_scores else 0
        
        # Calculate venue distribution
        venues = [s.get('venue', 'Unknown') for s in primary_sessions]
        venue_counts = {}
        for venue in venues:
            venue_counts[venue] = venue_counts.get(venue, 0) + 1
        
        return {
            'total_sessions': len(all_sessions),
            'scheduled_sessions': len(primary_sessions),
            'backup_sessions': total_backups,
            'average_score': round(avg_score, 3),
            'venue_distribution': venue_counts,
            'keyword_coverage': self._calculate_keyword_coverage(primary_sessions)
        }
    
    def _calculate_keyword_coverage(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate how many sessions cover each keyword"""
        keyword_counts = {}
        
        for session in sessions:
            keywords = session.get('keywords_matched', [])
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        return keyword_counts
    
    def _generate_schedule_summary(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall schedule summary"""
        total_sessions = 0
        total_backups = 0
        all_scores = []
        all_venues = []
        all_keywords = {}
        
        for date, daily_schedule in schedule.items():
            if date == 'summary':
                continue
            
            stats = daily_schedule.get('statistics', {})
            total_sessions += stats.get('scheduled_sessions', 0)
            total_backups += stats.get('backup_sessions', 0)
            
            # Collect scores
            for session in daily_schedule.get('primary_sessions', []):
                score = session.get('score', 0)
                if score > 0:
                    all_scores.append(score)
            
            # Collect venues
            venue_dist = stats.get('venue_distribution', {})
            for venue, count in venue_dist.items():
                all_venues.extend([venue] * count)
            
            # Collect keywords
            keyword_coverage = stats.get('keyword_coverage', {})
            for keyword, count in keyword_coverage.items():
                all_keywords[keyword] = all_keywords.get(keyword, 0) + count
        
        # Calculate overall statistics
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        venue_distribution = {}
        for venue in all_venues:
            venue_distribution[venue] = venue_distribution.get(venue, 0) + 1
        
        return {
            'total_conference_days': len([k for k in schedule.keys() if k != 'summary']),
            'total_scheduled_sessions': total_sessions,
            'total_backup_sessions': total_backups,
            'average_session_score': round(avg_score, 3),
            'overall_venue_distribution': venue_distribution,
            'overall_keyword_coverage': all_keywords,
            'schedule_efficiency': round(total_sessions / (len(schedule) - 1) if len(schedule) > 1 else 0, 1)
        }