"""
Venue filter for AWS re:Invent sessions
"""

import re
from typing import List, Dict, Any
from config import Config


class VenueFilter:
    def __init__(self, excluded_venues: List[str] = None):
        # Use ALLOWED_VENUES if available, otherwise fall back to EXCLUDED_VENUES
        if hasattr(Config, 'ALLOWED_VENUES') and Config.ALLOWED_VENUES:
            self.allowed_venues = [venue.lower() for venue in Config.ALLOWED_VENUES]
            self.allowed_patterns = self._compile_allowed_patterns()
            self.use_allowlist = True
            print(f"🏢 Using venue allowlist: {Config.ALLOWED_VENUES}")
        else:
            # Fall back to exclusion list
            venues_to_exclude = excluded_venues or Config.EXCLUDED_VENUES
            self.excluded_venues = [venue.lower() for venue in venues_to_exclude]
            self.exclusion_patterns = self._compile_exclusion_patterns()
            self.use_allowlist = False
            print(f"🏢 Using venue exclusion list: {venues_to_exclude}")
    
    def _compile_allowed_patterns(self):
        """Compile regex patterns for venue allowlist"""
        patterns = []
        for venue in self.allowed_venues:
            # Create pattern that matches venue name variations
            pattern = rf'\b{re.escape(venue)}\b'
            patterns.append(re.compile(pattern, re.IGNORECASE))
        return patterns
    
    def _compile_exclusion_patterns(self):
        """Compile regex patterns for venue exclusion"""
        patterns = []
        for venue in self.excluded_venues:
            # Create pattern that matches venue name variations
            pattern = rf'\b{re.escape(venue)}\b'
            patterns.append(re.compile(pattern, re.IGNORECASE))
        return patterns
    
    def filter_sessions(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter sessions by venue (either allowlist or blocklist)"""
        if self.use_allowlist:
            return self._filter_by_allowlist(sessions)
        else:
            return self._filter_by_blocklist(sessions)
    
    def _filter_by_allowlist(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only sessions at allowed venues"""
        filtered_sessions = []
        excluded_count = 0
        
        for session in sessions:
            if self._is_allowed_venue(session):
                filtered_sessions.append(session)
            else:
                excluded_count += 1
        
        print(f"✅ Venue allowlist filter: Kept {len(filtered_sessions)} sessions, excluded {excluded_count}")
        return filtered_sessions
    
    def _filter_by_blocklist(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out sessions at excluded venues"""
        filtered_sessions = []
        excluded_count = 0
        
        for session in sessions:
            if not self._is_excluded_venue(session):
                filtered_sessions.append(session)
            else:
                excluded_count += 1
        
        print(f"✅ Venue exclusion filter: Kept {len(filtered_sessions)} sessions, excluded {excluded_count}")
        return filtered_sessions
    
    def _is_allowed_venue(self, session: Dict[str, Any]) -> bool:
        """Check if session is at an allowed venue"""
        venue = session.get('venue', '')
        room = session.get('room', '')
        
        # Combine venue and room information
        location_text = f"{venue} {room}".strip()
        
        if not location_text:
            # If no venue information, exclude by default
            return False
        
        # Check against allowed patterns
        for pattern in self.allowed_patterns:
            if pattern.search(location_text):
                return True
        
        return False
    
    def _is_excluded_venue(self, session: Dict[str, Any]) -> bool:
        """Check if session is at an excluded venue"""
        venue = session.get('venue', '')
        room = session.get('room', '')
        
        # Combine venue and room information
        location_text = f"{venue} {room}".strip()
        
        if not location_text:
            # If no venue information, don't exclude
            return False
        
        # Check against exclusion patterns
        for pattern in self.exclusion_patterns:
            if pattern.search(location_text):
                return True
        
        return False
    
    def get_excluded_sessions(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get list of sessions that would be excluded"""
        excluded_sessions = []
        
        for session in sessions:
            if self.use_allowlist:
                if not self._is_allowed_venue(session):
                    excluded_sessions.append(session)
            else:
                if self._is_excluded_venue(session):
                    excluded_sessions.append(session)
        
        return excluded_sessions
    
    def get_venue_statistics(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics on venue distribution"""
        venue_counts = {}
        excluded_counts = {}
        
        for session in sessions:
            venue = session.get('venue', 'Unknown')
            
            # Count all venues
            venue_counts[venue] = venue_counts.get(venue, 0) + 1
            
            # Count excluded venues
            should_exclude = False
            if self.use_allowlist:
                should_exclude = not self._is_allowed_venue(session)
            else:
                should_exclude = self._is_excluded_venue(session)
            
            if should_exclude:
                excluded_counts[venue] = excluded_counts.get(venue, 0) + 1
        
        return {
            'all_venues': venue_counts,
            'excluded_venues': excluded_counts
        }
    
    def validate_venue_exclusions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that venue filtering is working correctly"""
        stats = self.get_venue_statistics(sessions)
        excluded_sessions = self.get_excluded_sessions(sessions)
        
        validation_report = {
            'total_sessions': len(sessions),
            'excluded_sessions': len(excluded_sessions),
            'exclusion_rate': len(excluded_sessions) / len(sessions) if sessions else 0,
            'excluded_venues': list(stats['excluded_venues'].keys()),
            'venue_breakdown': stats['all_venues'],
            'filter_type': 'allowlist' if self.use_allowlist else 'blocklist'
        }
        
        return validation_report