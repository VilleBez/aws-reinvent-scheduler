"""
Session scorer for AWS re:Invent sessions
"""

from typing import List, Dict, Any
from .keyword_filter import KeywordFilter


class SessionScorer:
    def __init__(self):
        self.scoring_weights = {
            'keyword_relevance': 0.40,  # 40% - Keyword match importance
            'session_level': 0.20,      # 20% - Session difficulty level
            'venue_convenience': 0.20,  # 20% - Venue location convenience
            'speaker_reputation': 0.10, # 10% - Speaker quality
            'session_uniqueness': 0.10  # 10% - Uniqueness/rarity
        }
        
        # Venue convenience mapping (higher is better)
        self.venue_convenience_scores = {
            'venetian': 0.9,
            'palazzo': 0.9,
            'wynn': 0.8,
            'encore': 0.8,
            'aria': 0.7,
            'bellagio': 0.7,
            'caesars': 0.6,
            'mirage': 0.6,
            'treasure island': 0.5,
            'flamingo': 0.5,
            'linq': 0.4,
            'paris': 0.4,
            'bally': 0.3,
            'harrah': 0.3,
            'rio': 0.2,
            'orleans': 0.2,
            'mgm grand': 0.0,  # Excluded venue
            'mandalay bay': 0.0  # Excluded venue
        }
        
        # Session level preferences (intermediate preferred)
        self.level_scores = {
            'beginner': 0.6,
            'intermediate': 1.0,
            'advanced': 0.8,
            'expert': 0.7
        }
    
    def score_sessions(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score all sessions and add score information"""
        scored_sessions = []
        
        for session in sessions:
            scored_session = session.copy()
            score_breakdown = self._calculate_session_score(session)
            
            scored_session['score'] = score_breakdown['total_score']
            scored_session['score_breakdown'] = score_breakdown
            
            scored_sessions.append(scored_session)
        
        # Sort by score (highest first)
        scored_sessions.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"Session scoring: Scored {len(scored_sessions)} sessions")
        if scored_sessions:
            print(f"Score range: {scored_sessions[-1]['score']:.2f} - {scored_sessions[0]['score']:.2f}")
        
        return scored_sessions
    
    def _calculate_session_score(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive score for a session"""
        scores = {
            'keyword_score': self._score_keyword_relevance(session),
            'level_score': self._score_session_level(session),
            'venue_score': self._score_venue_convenience(session),
            'speaker_score': self._score_speaker_reputation(session),
            'uniqueness_score': self._score_session_uniqueness(session)
        }
        
        # Calculate weighted total
        total_score = (
            scores['keyword_score'] * self.scoring_weights['keyword_relevance'] +
            scores['level_score'] * self.scoring_weights['session_level'] +
            scores['venue_score'] * self.scoring_weights['venue_convenience'] +
            scores['speaker_score'] * self.scoring_weights['speaker_reputation'] +
            scores['uniqueness_score'] * self.scoring_weights['session_uniqueness']
        )
        
        return {
            'total_score': round(total_score, 3),
            'component_scores': scores,
            'weights_used': self.scoring_weights
        }
    
    def _score_keyword_relevance(self, session: Dict[str, Any]) -> float:
        """Score based on keyword matches"""
        matched_keywords = session.get('keywords_matched', [])
        
        if not matched_keywords:
            return 0.0
        
        # Base score for having matches
        base_score = 0.5
        
        # Bonus for multiple matches
        match_bonus = min(0.3, len(matched_keywords) * 0.1)
        
        # Title match bonus
        title = session.get('title', '').lower()
        title_bonus = 0.0
        for keyword in matched_keywords:
            if keyword in title:
                title_bonus += 0.1
        
        title_bonus = min(0.2, title_bonus)
        
        return min(1.0, base_score + match_bonus + title_bonus)
    
    def _score_session_level(self, session: Dict[str, Any]) -> float:
        """Score based on session difficulty level"""
        level = (session.get('level') or '').lower()
        
        if not level:
            return 0.5  # Neutral score for unknown level
        
        return self.level_scores.get(level, 0.5)
    
    def _score_venue_convenience(self, session: Dict[str, Any]) -> float:
        """Score based on venue convenience"""
        venue = (session.get('venue') or '').lower()
        
        if not venue:
            return 0.5  # Neutral score for unknown venue
        
        # Find best matching venue
        best_score = 0.5
        for venue_name, score in self.venue_convenience_scores.items():
            if venue_name in venue:
                best_score = max(best_score, score)
        
        return best_score
    
    def _score_speaker_reputation(self, session: Dict[str, Any]) -> float:
        """Score based on speaker reputation (simplified)"""
        speakers = session.get('speakers') or []
        
        if not speakers:
            return 0.5  # Neutral score for no speaker info
        
        # Simple heuristic: more speakers might indicate higher profile session
        speaker_count_bonus = min(0.3, len(speakers) * 0.1)
        
        # Check for AWS employee indicators
        aws_bonus = 0.0
        for speaker in speakers:
            speaker_lower = speaker.lower()
            if any(indicator in speaker_lower for indicator in ['aws', 'amazon', 'principal', 'senior']):
                aws_bonus += 0.1
        
        aws_bonus = min(0.2, aws_bonus)
        
        return min(1.0, 0.5 + speaker_count_bonus + aws_bonus)
    
    def _score_session_uniqueness(self, session: Dict[str, Any]) -> float:
        """Score based on session uniqueness/rarity"""
        title = session.get('title', '').lower()
        description = (session.get('description') or '').lower()
        
        # Keywords that indicate unique/special sessions
        unique_indicators = [
            'new', 'preview', 'announcement', 'launch', 'exclusive',
            'deep dive', 'hands-on', 'workshop', 'lab', 'demo',
            'case study', 'real-world', 'production', 'scale'
        ]
        
        uniqueness_score = 0.5  # Base score
        
        for indicator in unique_indicators:
            if indicator in title:
                uniqueness_score += 0.1
            elif indicator in description:
                uniqueness_score += 0.05
        
        return min(1.0, uniqueness_score)
    
    def get_top_sessions(self, sessions: List[Dict[str, Any]], count: int = 10) -> List[Dict[str, Any]]:
        """Get top N sessions by score"""
        return sorted(sessions, key=lambda x: x.get('score', 0), reverse=True)[:count]
    
    def get_sessions_by_score_range(self, sessions: List[Dict[str, Any]], 
                                   min_score: float, max_score: float) -> List[Dict[str, Any]]:
        """Get sessions within a score range"""
        return [s for s in sessions if min_score <= s.get('score', 0) <= max_score]
    
    def get_scoring_statistics(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics on session scoring"""
        if not sessions:
            return {}
        
        scores = [s.get('score', 0) for s in sessions]
        
        stats = {
            'total_sessions': len(sessions),
            'average_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'score_distribution': {
                'high (0.8-1.0)': len([s for s in scores if s >= 0.8]),
                'medium (0.6-0.8)': len([s for s in scores if 0.6 <= s < 0.8]),
                'low (0.0-0.6)': len([s for s in scores if s < 0.6])
            }
        }
        
        return stats