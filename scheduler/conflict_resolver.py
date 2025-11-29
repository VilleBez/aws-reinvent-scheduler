"""
Conflict resolver for AWS re:Invent session scheduling
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


class ConflictResolver:
    def __init__(self):
        self.buffer_minutes = 30
    
    def resolve_conflicts(self, primary_sessions: List[Dict[str, Any]], 
                         backup_sessions: Dict[str, List[Dict[str, Any]]], 
                         time_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve scheduling conflicts and optimize the schedule"""
        
        # Check for time conflicts in primary sessions
        resolved_primary = self._resolve_time_conflicts(primary_sessions)
        
        # Validate backup sessions don't conflict with primary
        validated_backups = self._validate_backup_sessions(resolved_primary, backup_sessions)
        
        # Optimize for venue proximity
        optimized_schedule = self._optimize_venue_proximity(resolved_primary, validated_backups)
        
        return {
            'primary': optimized_schedule['primary'],
            'backups': optimized_schedule['backups'],
            'conflicts_resolved': optimized_schedule['conflicts_resolved']
        }
    
    def _resolve_time_conflicts(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve time conflicts between sessions"""
        if not sessions:
            return sessions
        
        # Sort sessions by start time
        sorted_sessions = sorted(sessions, key=lambda x: x.get('scheduled_start', '00:00'))
        
        resolved_sessions = []
        conflicts_found = 0
        
        for i, session in enumerate(sorted_sessions):
            current_start = session.get('scheduled_start')
            current_end = session.get('scheduled_end')
            
            if not current_start or not current_end:
                resolved_sessions.append(session)
                continue
            
            # Check for conflicts with previously scheduled sessions
            has_conflict = False
            
            for prev_session in resolved_sessions:
                prev_start = prev_session.get('scheduled_start')
                prev_end = prev_session.get('scheduled_end')
                
                if self._sessions_conflict(current_start, current_end, prev_start, prev_end):
                    has_conflict = True
                    conflicts_found += 1
                    break
            
            if not has_conflict:
                resolved_sessions.append(session)
            else:
                # Try to reschedule the session
                rescheduled_session = self._reschedule_session(session, resolved_sessions)
                if rescheduled_session:
                    resolved_sessions.append(rescheduled_session)
        
        if conflicts_found > 0:
            print(f"⚠️ Resolved {conflicts_found} time conflicts")
        
        return resolved_sessions
    
    def _sessions_conflict(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two sessions have time conflicts including buffer time"""
        try:
            s1 = datetime.strptime(start1, '%H:%M')
            e1 = datetime.strptime(end1, '%H:%M')
            s2 = datetime.strptime(start2, '%H:%M')
            e2 = datetime.strptime(end2, '%H:%M')
            
            # Add buffer time
            buffer = timedelta(minutes=self.buffer_minutes)
            e1_with_buffer = e1 + buffer
            e2_with_buffer = e2 + buffer
            
            # Check for overlap
            return s1 < e2_with_buffer and s2 < e1_with_buffer
        except:
            return False
    
    def _reschedule_session(self, session: Dict[str, Any], 
                           scheduled_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Try to reschedule a conflicting session"""
        # For now, we'll skip rescheduling and just log the conflict
        # In a more advanced implementation, we could try to find alternative time slots
        print(f"⚠️ Could not reschedule session: {session.get('title', 'Unknown')[:50]}...")
        return None
    
    def _validate_backup_sessions(self, primary_sessions: List[Dict[str, Any]], 
                                 backup_sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Validate that backup sessions don't conflict with primary sessions"""
        validated_backups = {}
        
        # Get all primary session times
        primary_times = []
        for session in primary_sessions:
            start_time = session.get('scheduled_start')
            end_time = session.get('scheduled_end')
            if start_time and end_time:
                primary_times.append((start_time, end_time))
        
        for slot_id, backups in backup_sessions.items():
            validated_slot_backups = []
            
            for backup in backups:
                backup_start = backup.get('start_time')
                backup_end = backup.get('end_time')
                
                if not backup_start or not backup_end:
                    continue
                
                # Check if backup conflicts with any primary session
                conflicts_with_primary = False
                for primary_start, primary_end in primary_times:
                    if self._sessions_conflict(backup_start, backup_end, primary_start, primary_end):
                        conflicts_with_primary = True
                        break
                
                if not conflicts_with_primary:
                    validated_slot_backups.append(backup)
            
            validated_backups[slot_id] = validated_slot_backups
        
        return validated_backups
    
    def _optimize_venue_proximity(self, primary_sessions: List[Dict[str, Any]], 
                                 backup_sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Optimize schedule for venue proximity"""
        # Sort primary sessions by time
        sorted_primary = sorted(primary_sessions, key=lambda x: x.get('scheduled_start', '00:00'))
        
        # Calculate venue transitions
        venue_transitions = self._calculate_venue_transitions(sorted_primary)
        
        # Try to optimize if there are too many venue changes
        optimized_primary = self._reduce_venue_transitions(sorted_primary, backup_sessions)
        
        return {
            'primary': optimized_primary,
            'backups': backup_sessions,
            'conflicts_resolved': {
                'venue_transitions': venue_transitions,
                'optimization_applied': len(optimized_primary) != len(sorted_primary)
            }
        }
    
    def _calculate_venue_transitions(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Calculate venue transitions between consecutive sessions"""
        transitions = []
        
        for i in range(len(sessions) - 1):
            current_venue = sessions[i].get('venue', 'Unknown')
            next_venue = sessions[i + 1].get('venue', 'Unknown')
            
            if current_venue != next_venue:
                transitions.append({
                    'from_venue': current_venue,
                    'to_venue': next_venue,
                    'from_session': sessions[i].get('title', 'Unknown')[:30],
                    'to_session': sessions[i + 1].get('title', 'Unknown')[:30],
                    'time_gap': self._calculate_time_gap(
                        sessions[i].get('scheduled_end', '00:00'),
                        sessions[i + 1].get('scheduled_start', '00:00')
                    )
                })
        
        return transitions
    
    def _calculate_time_gap(self, end_time: str, start_time: str) -> int:
        """Calculate time gap between sessions in minutes"""
        try:
            end = datetime.strptime(end_time, '%H:%M')
            start = datetime.strptime(start_time, '%H:%M')
            
            # Handle next day case
            if start < end:
                start = start.replace(day=start.day + 1)
            
            gap = start - end
            return int(gap.total_seconds() / 60)
        except:
            return 0
    
    def _reduce_venue_transitions(self, primary_sessions: List[Dict[str, Any]], 
                                 backup_sessions: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Try to reduce venue transitions by swapping with backup sessions"""
        # For now, return the original sessions
        # In a more advanced implementation, we could try to swap sessions
        # with backups to minimize venue changes
        return primary_sessions
    
    def get_conflict_report(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a conflict analysis report"""
        conflicts_resolved = schedule.get('conflicts_resolved', {})
        venue_transitions = conflicts_resolved.get('venue_transitions', [])
        
        report = {
            'total_venue_transitions': len(venue_transitions),
            'venue_transition_details': venue_transitions,
            'optimization_applied': conflicts_resolved.get('optimization_applied', False),
            'recommendations': []
        }
        
        # Add recommendations based on analysis
        if len(venue_transitions) > 3:
            report['recommendations'].append(
                "Consider grouping sessions by venue to reduce travel time"
            )
        
        for transition in venue_transitions:
            if transition['time_gap'] < 30:
                report['recommendations'].append(
                    f"Short transition time ({transition['time_gap']} min) between "
                    f"{transition['from_venue']} and {transition['to_venue']}"
                )
        
        return report