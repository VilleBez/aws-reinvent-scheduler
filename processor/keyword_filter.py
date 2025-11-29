"""
Keyword filter for AWS re:Invent sessions
"""

import re
from typing import List, Dict, Any


class KeywordFilter:
    def __init__(self, keywords: List[str]):
        self.keywords = [keyword.lower() for keyword in keywords]
        self.keyword_patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient keyword matching"""
        patterns = {}
        for keyword in self.keywords:
            # Create pattern that matches whole words and variations
            pattern = rf'\b{re.escape(keyword)}\b'
            patterns[keyword] = re.compile(pattern, re.IGNORECASE)
        return patterns
    
    def filter_sessions(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter sessions based on keyword matches"""
        filtered_sessions = []
        
        for session in sessions:
            if self._matches_keywords(session):
                filtered_sessions.append(session)
        
        print(f"Keyword filter: {len(filtered_sessions)}/{len(sessions)} sessions match interest keywords")
        return filtered_sessions
    
    def _matches_keywords(self, session: Dict[str, Any]) -> bool:
        """Check if session matches any of the interest keywords"""
        # Text fields to search
        searchable_fields = [
            session.get('title', ''),
            session.get('description', ''),
            session.get('track', ''),
            session.get('session_type', '')
        ]
        
        # Combine all searchable text
        combined_text = ' '.join(filter(None, searchable_fields))
        
        if not combined_text:
            return False
        
        matched_keywords = []
        
        # Check each keyword pattern
        for keyword, pattern in self.keyword_patterns.items():
            if pattern.search(combined_text):
                matched_keywords.append(keyword)
        
        # Update session with matched keywords
        session['keywords_matched'] = matched_keywords
        
        # Return True if any keywords matched
        return len(matched_keywords) > 0
    
    def get_keyword_matches(self, session: Dict[str, Any]) -> List[str]:
        """Get list of keywords that match a session"""
        return session.get('keywords_matched', [])
    
    def calculate_keyword_score(self, session: Dict[str, Any]) -> float:
        """Calculate a score based on keyword matches"""
        matched_keywords = session.get('keywords_matched', [])
        
        if not matched_keywords:
            return 0.0
        
        # Base score for having any matches
        base_score = 0.5
        
        # Additional score based on number of matches
        match_bonus = len(matched_keywords) * 0.2
        
        # Bonus for title matches (higher weight)
        title_matches = self._count_title_matches(session)
        title_bonus = title_matches * 0.3
        
        # Total score (capped at 1.0)
        total_score = min(1.0, base_score + match_bonus + title_bonus)
        
        return total_score
    
    def _count_title_matches(self, session: Dict[str, Any]) -> int:
        """Count keyword matches specifically in the title"""
        title = session.get('title', '')
        if not title:
            return 0
        
        title_matches = 0
        for keyword, pattern in self.keyword_patterns.items():
            if pattern.search(title):
                title_matches += 1
        
        return title_matches
    
    def get_sessions_by_keyword(self, sessions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group sessions by matched keywords"""
        keyword_groups = {keyword: [] for keyword in self.keywords}
        
        for session in sessions:
            matched_keywords = session.get('keywords_matched', [])
            for keyword in matched_keywords:
                if keyword in keyword_groups:
                    keyword_groups[keyword].append(session)
        
        return keyword_groups
    
    def get_keyword_statistics(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics on keyword matches"""
        stats = {keyword: 0 for keyword in self.keywords}
        
        for session in sessions:
            matched_keywords = session.get('keywords_matched', [])
            for keyword in matched_keywords:
                if keyword in stats:
                    stats[keyword] += 1
        
        return stats