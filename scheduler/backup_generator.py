"""
Backup session generator for AWS re:Invent scheduling
"""

from typing import List, Dict, Any
from config import Config


class BackupGenerator:
    def __init__(self):
        self.min_backup_sessions = Config.MIN_BACKUP_SESSIONS
    
    def generate_backups(self, all_sessions: List[Dict[str, Any]], 
                        primary_sessions: List[Dict[str, Any]], 
                        time_slots: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate backup sessions for each time slot"""
        backup_sessions = {}
        
        # Get IDs of primary sessions to exclude them from backups
        primary_session_ids = {s.get('session_id') for s in primary_sessions}
        
        for slot in time_slots:
            slot_id = slot['slot_id']
            slot_start = slot['start_time']
            slot_end = slot['end_time']
            
            # Find sessions that could fit in this time slot
            candidate_sessions = self._find_candidate_sessions(
                all_sessions, slot_start, slot_end, primary_session_ids
            )
            
            # Score and rank backup candidates
            ranked_backups = self._rank_backup_candidates(candidate_sessions, slot)
            
            # Select top backup sessions
            selected_backups = ranked_backups[:max(self.min_backup_sessions, 3)]
            
            backup_sessions[slot_id] = selected_backups
        
        self._log_backup_statistics(backup_sessions)
        return backup_sessions
    
    def _find_candidate_sessions(self, all_sessions: List[Dict[str, Any]], 
                                slot_start: str, slot_end: str, 
                                exclude_ids: set) -> List[Dict[str, Any]]:
        """Find sessions that could serve as backups for a time slot"""
        candidates = []
        
        for session in all_sessions:
            session_id = session.get('session_id')
            
            # Skip if already scheduled as primary
            if session_id in exclude_ids:
                continue
            
            # Check if session could fit in the time slot
            if self._session_fits_slot(session, slot_start, slot_end):
                candidates.append(session)
        
        return candidates
    
    def _session_fits_slot(self, session: Dict[str, Any], 
                          slot_start: str, slot_end: str) -> bool:
        """Check if a session could fit in a time slot"""
        session_start = session.get('start_time')
        session_end = session.get('end_time')
        
        if not session_start or not session_end:
            return False
        
        # For backup sessions, we're more flexible with timing
        # Allow sessions that are close to the slot time
        return self._times_are_compatible(session_start, session_end, slot_start, slot_end)
    
    def _times_are_compatible(self, session_start: str, session_end: str, 
                             slot_start: str, slot_end: str) -> bool:
        """Check if session times are compatible with slot times"""
        try:
            from datetime import datetime
            
            s_start = datetime.strptime(session_start, '%H:%M')
            s_end = datetime.strptime(session_end, '%H:%M')
            slot_s = datetime.strptime(slot_start, '%H:%M')
            slot_e = datetime.strptime(slot_end, '%H:%M')
            
            # Allow some flexibility (±30 minutes)
            flexibility_minutes = 30
            from datetime import timedelta
            flex = timedelta(minutes=flexibility_minutes)
            
            # Check if session times are within flexibility range of slot times
            start_compatible = abs((s_start - slot_s).total_seconds()) <= flex.total_seconds()
            end_compatible = abs((s_end - slot_e).total_seconds()) <= flex.total_seconds()
            
            return start_compatible and end_compatible
        except:
            return False
    
    def _rank_backup_candidates(self, candidates: List[Dict[str, Any]], 
                               slot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank backup candidates by suitability"""
        if not candidates:
            return []
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            backup_score = self._calculate_backup_score(candidate, slot)
            candidate_copy = candidate.copy()
            candidate_copy['backup_score'] = backup_score
            scored_candidates.append(candidate_copy)
        
        # Sort by backup score (highest first)
        scored_candidates.sort(key=lambda x: x['backup_score'], reverse=True)
        
        return scored_candidates
    
    def _calculate_backup_score(self, session: Dict[str, Any], 
                               slot: Dict[str, Any]) -> float:
        """Calculate backup suitability score for a session"""
        # Base score from session's original score
        base_score = session.get('score', 0) * 0.7  # Slightly lower weight for backups
        
        # Time compatibility bonus
        time_bonus = self._calculate_time_compatibility_bonus(session, slot)
        
        # Keyword diversity bonus (prefer different topics for variety)
        diversity_bonus = self._calculate_diversity_bonus(session)
        
        # Venue convenience bonus
        venue_bonus = self._calculate_venue_bonus(session)
        
        total_score = base_score + time_bonus + diversity_bonus + venue_bonus
        return min(1.0, total_score)
    
    def _calculate_time_compatibility_bonus(self, session: Dict[str, Any], 
                                          slot: Dict[str, Any]) -> float:
        """Calculate bonus for time compatibility"""
        session_start = session.get('start_time')
        session_end = session.get('end_time')
        slot_start = slot['start_time']
        slot_end = slot['end_time']
        
        if not session_start or not session_end:
            return 0.0
        
        try:
            from datetime import datetime
            
            s_start = datetime.strptime(session_start, '%H:%M')
            s_end = datetime.strptime(session_end, '%H:%M')
            slot_s = datetime.strptime(slot_start, '%H:%M')
            slot_e = datetime.strptime(slot_end, '%H:%M')
            
            # Calculate time difference
            start_diff = abs((s_start - slot_s).total_seconds() / 60)  # minutes
            end_diff = abs((s_end - slot_e).total_seconds() / 60)  # minutes
            
            # Bonus decreases with time difference
            max_bonus = 0.2
            start_bonus = max(0, max_bonus - (start_diff / 60) * 0.1)
            end_bonus = max(0, max_bonus - (end_diff / 60) * 0.1)
            
            return (start_bonus + end_bonus) / 2
        except:
            return 0.0
    
    def _calculate_diversity_bonus(self, session: Dict[str, Any]) -> float:
        """Calculate bonus for topic diversity"""
        keywords = session.get('keywords_matched', [])
        
        # Bonus for having multiple keywords (indicates broader relevance)
        keyword_bonus = min(0.1, len(keywords) * 0.03)
        
        # Bonus for specific high-value keywords
        high_value_keywords = ['ai', 'architect', 'lakehouse', 'devops']
        high_value_bonus = 0.0
        for keyword in keywords:
            if keyword.lower() in high_value_keywords:
                high_value_bonus += 0.02
        
        return min(0.15, keyword_bonus + high_value_bonus)
    
    def _calculate_venue_bonus(self, session: Dict[str, Any]) -> float:
        """Calculate bonus for venue convenience"""
        venue = session.get('venue', '').lower()
        
        # Prefer venues that are more convenient
        venue_scores = {
            'venetian': 0.1,
            'palazzo': 0.1,
            'wynn': 0.08,
            'encore': 0.08,
            'aria': 0.06,
            'bellagio': 0.06,
            'caesars': 0.04,
            'mirage': 0.04
        }
        
        for venue_name, bonus in venue_scores.items():
            if venue_name in venue:
                return bonus
        
        return 0.02  # Small bonus for any known venue
    
    def _log_backup_statistics(self, backup_sessions: Dict[str, List[Dict[str, Any]]]):
        """Log statistics about generated backup sessions"""
        total_backups = sum(len(backups) for backups in backup_sessions.values())
        slots_with_backups = len([slot for slot, backups in backup_sessions.items() if backups])
        
        print(f"📋 Generated {total_backups} backup sessions across {slots_with_backups} time slots")
        
        # Check if minimum backup requirement is met
        insufficient_slots = []
        for slot_id, backups in backup_sessions.items():
            if len(backups) < self.min_backup_sessions:
                insufficient_slots.append(slot_id)
        
        if insufficient_slots:
            print(f"⚠️ {len(insufficient_slots)} slots have fewer than {self.min_backup_sessions} backup sessions")
    
    def get_backup_statistics(self, backup_sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get detailed statistics about backup sessions"""
        stats = {
            'total_backup_sessions': sum(len(backups) for backups in backup_sessions.values()),
            'slots_with_backups': len([slot for slot, backups in backup_sessions.items() if backups]),
            'average_backups_per_slot': 0,
            'slots_meeting_minimum': 0,
            'backup_score_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'keyword_coverage': {}
        }
        
        if backup_sessions:
            backup_counts = [len(backups) for backups in backup_sessions.values()]
            stats['average_backups_per_slot'] = sum(backup_counts) / len(backup_counts)
            
            # Count slots meeting minimum requirement
            stats['slots_meeting_minimum'] = len([
                slot for slot, backups in backup_sessions.items() 
                if len(backups) >= self.min_backup_sessions
            ])
            
            # Analyze backup scores and keywords
            all_backups = []
            for backups in backup_sessions.values():
                all_backups.extend(backups)
            
            for backup in all_backups:
                score = backup.get('backup_score', 0)
                if score >= 0.7:
                    stats['backup_score_distribution']['high'] += 1
                elif score >= 0.5:
                    stats['backup_score_distribution']['medium'] += 1
                else:
                    stats['backup_score_distribution']['low'] += 1
                
                # Count keyword coverage
                keywords = backup.get('keywords_matched', [])
                for keyword in keywords:
                    stats['keyword_coverage'][keyword] = stats['keyword_coverage'].get(keyword, 0) + 1
        
        return stats