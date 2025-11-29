"""
Data parser for AWS re:Invent session elements
"""

import re
from datetime import datetime
from bs4 import BeautifulSoup


class SessionDataParser:
    def __init__(self):
        self.date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\w+,?\s+\w+\s+\d{1,2},?\s+\d{4})',  # Month Day, Year
            r'(\w+\s+\d{1,2})',  # Month Day
        ]
        
        self.time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))',  # 12:00 PM
            r'(\d{1,2}:\d{2})',  # 24-hour format
        ]
    
    def parse_session_element(self, element):
        """Parse a session element and extract structured data"""
        try:
            # Get the HTML content
            html_content = element.get_attribute('outerHTML')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            session_data = {
                'session_id': self._extract_session_id(element, soup),
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'date': self._extract_date(soup),
                'start_time': self._extract_start_time(soup),
                'end_time': self._extract_end_time(soup),
                'duration_minutes': None,
                'venue': self._extract_venue(soup),
                'room': self._extract_room(soup),
                'session_type': self._extract_session_type(soup),
                'track': self._extract_track(soup),
                'speakers': self._extract_speakers(soup),
                'level': self._extract_level(soup),
                'prerequisites': self._extract_prerequisites(soup),
                'keywords_matched': [],
                # Additional fields for session_scorer.py
                'features': self._extract_features(soup),
                'topics': self._extract_topics(soup),
                'roles': self._extract_roles(soup),
                'area_of_interest': self._extract_area_of_interest(soup),
                'services': self._extract_services(soup)
            }
            
            # Calculate duration if start and end times are available
            if session_data['start_time'] and session_data['end_time']:
                session_data['duration_minutes'] = self._calculate_duration(
                    session_data['start_time'],
                    session_data['end_time']
                )
            
            # Debug output for first few sessions
            title = session_data.get('title', 'No title')
            venue = session_data.get('venue', 'No venue')
            date = session_data.get('date', 'No date')
            start_time = session_data.get('start_time', 'No start time')
            
            # Only print debug info for sessions that have missing critical data (first 5 only)
            if (not venue or not date or not start_time) and hasattr(self, '_debug_count'):
                if not hasattr(self, '_debug_count'):
                    self._debug_count = 0
                if self._debug_count < 5:
                    print(f"DEBUG: Session '{title[:50]}...' - venue: {venue}, date: {date}, start_time: {start_time}")
                    self._debug_count += 1
            
            return session_data
            
        except Exception as e:
            print(f"Error parsing session element: {e}")
            return None
    
    def _extract_session_id(self, element, soup):
        """Extract session ID from element attributes or content"""
        # Try data attributes first
        session_id = element.get_attribute('data-session-id')
        if session_id:
            return session_id
        
        # Try other common attributes
        for attr in ['id', 'data-id', 'data-event-id']:
            value = element.get_attribute(attr)
            if value:
                return value
        
        # Try to find in text content
        text = soup.get_text()
        id_match = re.search(r'(?:Session|ID):\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if id_match:
            return id_match.group(1)
        
        return None
    
    def _extract_title(self, soup):
        """Extract session title"""
        # 1. Try AWS re:Invent specific selector first
        title_element = soup.select_one('.title-text')
        if title_element:
            title = title_element.get_text(strip=True)
            if title:
                return title
        
        # 2. Try other title selectors
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.title', '.session-title', '.event-title',
            '[data-title]', '.name', '.session-name',
            'a[href*="session"]', 'a[href*="event"]'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                title = element.get_text(strip=True)
                if title and len(title) > 10 and len(title) < 200:  # Reasonable title length
                    return title
        
        # 3. Try to find text that looks like a session title
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        
        for line in lines:
            # Look for lines that contain session codes (like AIM357-S, DVT222-S, etc.)
            if re.search(r'\([A-Z]{3}\d{3}[-\w]*\)', line):
                return line
            # Look for lines that are likely titles (reasonable length, contains keywords)
            if (20 < len(line) < 150 and
                any(keyword in line.lower() for keyword in ['aws', 'amazon', 'cloud', 'ai', 'ml', 'data'])):
                return line
        
        # 4. Fallback: return the first substantial text
        for line in lines:
            if 15 < len(line) < 100:
                return line
        
        return None
    
    def _extract_description(self, soup):
        """Extract session description"""
        # 1. Try AWS re:Invent specific description selector first
        desc_element = soup.select_one('div.description')
        if desc_element:
            desc = desc_element.get_text(strip=True)
            if desc and len(desc) > 20:
                return desc
        
        # 2. Try other description selectors
        description_selectors = [
            '.description', '.summary', '.abstract',
            '.content', '.details', 'p'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                desc = element.get_text(strip=True)
                if desc and len(desc) > 20:  # Reasonable description length
                    return desc
        
        return None
    
    def _extract_date(self, soup):
        """Extract session date"""
        # 1. Try AWS re:Invent specific selector first
        date_element = soup.select_one('.session-date')
        if date_element:
            date_text = date_element.get_text(strip=True)
            # Parse "Tuesday, Dec 2" format
            date_match = re.search(r'(\w+),?\s+Dec\s+(\d+)', date_text, re.IGNORECASE)
            if date_match:
                day = date_match.group(2)
                return f'2025-12-{day.zfill(2)}'
        
        # 2. Try badge selector for day information
        day_badge = soup.select_one('.badge.rf-day')
        if day_badge:
            badge_text = day_badge.get_text(strip=True)
            # Parse "Tuesday, Dec 02" format from badge
            date_match = re.search(r'(\w+),?\s+Dec\s+(\d+)', badge_text, re.IGNORECASE)
            if date_match:
                day = date_match.group(2)
                return f'2025-12-{day.zfill(2)}'
        
        # 3. Try time badge selector for date information
        time_badge = soup.select_one('.badge.rf-time')
        if time_badge:
            badge_text = time_badge.get_text(strip=True)
            # Parse "11:00 a.m. Tuesday, Dec 02" format from time badge
            date_match = re.search(r'(\w+),?\s+Dec\s+(\d+)', badge_text, re.IGNORECASE)
            if date_match:
                day = date_match.group(2)
                return f'2025-12-{day.zfill(2)}'
        
        # 4. Try CSS class-based date extraction from the li element
        if soup.name == 'li' and soup.get('class'):
            classes = soup.get('class', [])
            for class_name in classes:
                if class_name.startswith('day-'):
                    # Extract from "day-tuesday-dec-02" format
                    date_match = re.search(r'day-\w+-dec-(\d+)', class_name, re.IGNORECASE)
                    if date_match:
                        day = date_match.group(1)
                        return f'2025-12-{day.zfill(2)}'
        
        # 5. Get all text content and try patterns
        text = soup.get_text()
        
        date_patterns = [
            r'2025-12-0([1-5])',  # YYYY-MM-DD format
            r'December\s+([1-5]),?\s+2025',  # December 1, 2025
            r'Dec\s+([1-5]),?\s+2025',  # Dec 1, 2025
            r'12/0([1-5])/2025',  # MM/DD/YYYY
            r'([1-5])\s+December\s+2025',  # 1 December 2025
            r'([1-5])\s+Dec\s+2025',  # 1 Dec 2025
            r'Monday,?\s+Dec\s+([1-5])',  # Monday, Dec 1
            r'Tuesday,?\s+Dec\s+([1-5])',  # Tuesday, Dec 2
            r'Wednesday,?\s+Dec\s+([1-5])',  # Wednesday, Dec 3
            r'Thursday,?\s+Dec\s+([1-5])',  # Thursday, Dec 4
            r'Friday,?\s+Dec\s+([1-5])',  # Friday, Dec 5
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1)
                return f'2025-12-{day.zfill(2)}'
        
        # 3. Try other date selectors
        date_selectors = [
            '.date', '.event-date', '[data-date]', '.day', '.schedule-date'
        ]
        
        for selector in date_selectors:
            elements = soup.select(selector)
            for element in elements:
                date_text = element.get_text(strip=True)
                # Look for conference dates in the text
                for day in range(1, 6):
                    if f'Dec {day}' in date_text or f'December {day}' in date_text:
                        return f'2025-12-{str(day).zfill(2)}'
        
        return None
    
    def _extract_start_time(self, soup):
        """Extract session start time"""
        # 1. Try AWS re:Invent specific selector first
        time_element = soup.select_one('.session-time')
        if time_element:
            time_text = time_element.get_text(strip=True)
            # Parse "11:30 AM - 12:30 PM PST" format
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-–—]\s*(\d{1,2}:\d{2}\s*(?:AM|PM))', time_text, re.IGNORECASE)
            if time_match:
                return self._normalize_time(time_match.group(1))
        
        # 2. Try time badge selector
        time_badge = soup.select_one('.badge.rf-time')
        if time_badge:
            badge_text = time_badge.get_text(strip=True)
            # Parse "11:00 a.m. Tuesday, Dec 02" format from time badge
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|AM|PM))', badge_text, re.IGNORECASE)
            if time_match:
                time_str = time_match.group(1).replace('a.m.', 'AM').replace('p.m.', 'PM')
                return self._normalize_time(time_str)
        
        # 3. Get all text content and try patterns
        text = soup.get_text()
        
        time_range_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-–—]\s*(\d{1,2}:\d{2}\s*(?:AM|PM))',  # 11:30 AM - 12:30 PM
            r'(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})',  # 11:30 - 12:30 (24h)
            r'(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.))\s*[-–—]\s*(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.))',  # 11:30 a.m. - 12:30 p.m.
        ]
        
        for pattern in time_range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_str = match.group(1).replace('a.m.', 'AM').replace('p.m.', 'PM')
                return self._normalize_time(time_str)
        
        # 4. Try single time patterns
        single_time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))',  # 11:30 AM
            r'(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.))',  # 11:30 a.m.
            r'(\d{1,2}:\d{2})',  # 11:30
        ]
        
        for pattern in single_time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first reasonable time (between 7 AM and 8 PM)
                for time_str in matches:
                    time_str = time_str.replace('a.m.', 'AM').replace('p.m.', 'PM')
                    normalized = self._normalize_time(time_str)
                    if normalized:
                        hour = int(normalized.split(':')[0])
                        if 7 <= hour <= 20:  # Reasonable conference hours
                            return normalized
        
        # 5. Try other time selectors
        time_selectors = [
            '.time', '.start-time', '[data-time]', '.schedule-time'
        ]
        
        for selector in time_selectors:
            elements = soup.select(selector)
            for element in elements:
                time_text = element.get_text(strip=True)
                # Extract time from the element text
                for pattern in time_range_patterns + single_time_patterns:
                    match = re.search(pattern, time_text, re.IGNORECASE)
                    if match:
                        time_str = match.group(1).replace('a.m.', 'AM').replace('p.m.', 'PM')
                        return self._normalize_time(time_str)
        
        return None
    
    def _extract_end_time(self, soup):
        """Extract session end time"""
        # 1. Try AWS re:Invent specific selector first
        time_element = soup.select_one('.session-time')
        if time_element:
            time_text = time_element.get_text(strip=True)
            # Parse "11:30 AM - 12:30 PM PST" format
            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-–—]\s*(\d{1,2}:\d{2}\s*(?:AM|PM))', time_text, re.IGNORECASE)
            if time_match:
                return self._normalize_time(time_match.group(2))
        
        # 2. Get all text content and try patterns
        text = soup.get_text()
        
        time_range_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[-–—]\s*(\d{1,2}:\d{2}\s*(?:AM|PM))',  # 11:30 AM - 12:30 PM
            r'(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})',  # 11:30 - 12:30 (24h)
            r'(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.))\s*[-–—]\s*(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.))',  # 11:30 a.m. - 12:30 p.m.
        ]
        
        for pattern in time_range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_str = match.group(2).replace('a.m.', 'AM').replace('p.m.', 'PM')
                return self._normalize_time(time_str)
        
        # 3. Try other time selectors
        time_selectors = [
            '.time', '.end-time', '[data-time]', '.schedule-time'
        ]
        
        for selector in time_selectors:
            elements = soup.select(selector)
            for element in elements:
                time_text = element.get_text(strip=True)
                # Extract end time from the element text
                for pattern in time_range_patterns:
                    match = re.search(pattern, time_text, re.IGNORECASE)
                    if match:
                        time_str = match.group(2).replace('a.m.', 'AM').replace('p.m.', 'PM')
                        return self._normalize_time(time_str)
        
        # 4. If we have start time but no end time, estimate based on typical session lengths
        start_time = self._extract_start_time(soup)
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%H:%M')
                # Assume 60-minute sessions by default
                end_dt = start_dt.replace(hour=start_dt.hour + 1)
                return end_dt.strftime('%H:%M')
            except:
                pass
        
        return None
    
    def _extract_venue(self, soup):
        """Extract venue information"""
        # 1. Try AWS re:Invent specific location selector first - nested span structure
        location_element = soup.select_one('.session-location span span')
        if location_element:
            location_text = location_element.get_text(strip=True)
            if '|' in location_text:
                # Parse "Venetian | Level 2 | Venetian Ballroom E | Content Hub | Red Theater"
                parts = [part.strip() for part in location_text.split('|')]
                if parts and parts[0]:
                    return parts[0]  # Return the venue (first part)
        
        # 2. Try single span selector
        location_element = soup.select_one('.session-location span')
        if location_element:
            location_text = location_element.get_text(strip=True)
            if '|' in location_text:
                # Parse "Venetian | Level 3 | Murano 3201B"
                parts = [part.strip() for part in location_text.split('|')]
                if parts and parts[0]:
                    return parts[0]  # Return the venue (first part)
        
        # 3. Try venue badge selector
        venue_badge = soup.select_one('.badge.rf-venue')
        if venue_badge:
            venue_text = venue_badge.get_text(strip=True)
            if venue_text:
                return venue_text
        
        # 4. Try CSS class-based venue extraction from the li element
        if soup.name == 'li' and soup.get('class'):
            classes = soup.get('class', [])
            for class_name in classes:
                if class_name.startswith('venue-'):
                    venue_name = class_name.replace('venue-', '').replace('-', ' ').title()
                    return venue_name
        
        # 5. Try other location selectors
        location_selectors = [
            '.session-location', '.location', '.venue', '.building', '[data-venue]'
        ]
        
        for selector in location_selectors:
            elements = soup.select(selector)
            for element in elements:
                location_text = element.get_text(strip=True)
                if '|' in location_text:
                    parts = [part.strip() for part in location_text.split('|')]
                    if parts and parts[0]:
                        return parts[0]  # Return the venue (first part)
                elif location_text:
                    # Check if it's a known venue
                    for venue in ['Venetian', 'Caesars Forum', 'Wynn', 'Aria', 'Bellagio', 'MGM Grand', 'Mandalay Bay']:
                        if venue.lower() in location_text.lower():
                            return venue
        
        # 6. Try text patterns
        text = soup.get_text()
        venue_patterns = [
            r'\b(Venetian|Caesars Forum|Caesars Palace|Wynn|Aria|Bellagio|MGM Grand|Mandalay Bay|Paris|Flamingo|Horseshoe|Linq)\b',
            r'(?:Venue|Location|Building):\s*([^,\n|]+)',
            r'(?:at|@)\s+(Venetian|Caesars Forum|Caesars Palace|Wynn|Aria|Bellagio|MGM Grand|Mandalay Bay)',
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                venue = match.group(1).strip()
                if venue:
                    return venue
        
        return None
    
    def _extract_room(self, soup):
        """Extract room information"""
        # Try AWS re:Invent specific location selector first - nested span structure
        location_element = soup.select_one('.session-location span span')
        if location_element:
            location_text = location_element.get_text(strip=True)
            # Parse "Venetian | Level 2 | Venetian Ballroom E | Content Hub | Red Theater"
            parts = [part.strip() for part in location_text.split('|')]
            if len(parts) >= 3:
                # Combine all parts after venue as room info
                room_parts = parts[1:]  # Everything after venue
                return ' | '.join(room_parts)
            elif len(parts) >= 2:
                return parts[1]  # Return the level/room (second part)
        
        # Try single span selector
        location_element = soup.select_one('.session-location span')
        if location_element:
            location_text = location_element.get_text(strip=True)
            # Parse "Venetian | Level 3 | Murano 3201B"
            parts = [part.strip() for part in location_text.split('|')]
            if len(parts) >= 3:
                return parts[2]  # Return the room (third part)
            elif len(parts) >= 2:
                return parts[1]  # Return the level/room (second part)
        
        # Fallback to general room selectors
        room_selectors = [
            '.room', '.hall', '[data-room]'
        ]
        
        for selector in room_selectors:
            element = soup.select_one(selector)
            if element:
                room = element.get_text(strip=True)
                if room:
                    return room
        
        # Try to find room in text
        text = soup.get_text()
        room_patterns = [
            r'(?:Room|Hall):\s*([^,\n]+)',
            r'\|\s*([^|]+)\s*$',  # Last part after pipe separator
            r'Level\s+\d+\s*\|\s*([^|]+)',  # Room after "Level X |"
        ]
        
        for pattern in room_patterns:
            room_match = re.search(pattern, text, re.IGNORECASE)
            if room_match:
                room = room_match.group(1).strip()
                if room and len(room) > 2:  # Reasonable room name length
                    return room
        
        return None
    
    def _extract_session_type(self, soup):
        """Extract session type (e.g., Keynote, Breakout, Workshop)"""
        # Try AWS re:Invent specific attribute selector first
        type_element = soup.select_one('.attribute-Type [data-test="attribute-values"]')
        if type_element:
            session_type = type_element.get_text(strip=True)
            if session_type:
                return session_type
        
        # Try alternative attribute selectors
        alt_selectors = [
            '.attribute-Type .attribute-value',
            '.attribute-Type span',
            '[data-attribute="Type"]',
            '.session-type-badge'
        ]
        
        for selector in alt_selectors:
            element = soup.select_one(selector)
            if element:
                session_type = element.get_text(strip=True)
                if session_type:
                    return session_type
        
        # Fallback to general type selectors
        type_selectors = [
            '.type', '.category', '.session-type', '[data-type]'
        ]
        
        for selector in type_selectors:
            element = soup.select_one(selector)
            if element:
                session_type = element.get_text(strip=True)
                if session_type:
                    return session_type
        
        # Try to extract from text patterns
        text = soup.get_text()
        type_patterns = [
            r'Type:\s*([^,\n]+)',
            r'\b(Keynote|Breakout|Workshop|Lightning Talk|Chalk Talk|Demo|Panel)\b'
        ]
        
        for pattern in type_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                session_type = match.group(1).strip()
                if session_type:
                    return session_type
        
        return None
    
    def _extract_track(self, soup):
        """Extract track information"""
        # Try AWS re:Invent specific attribute selector first
        track_element = soup.select_one('.attribute-Track [data-test="attribute-values"]')
        if track_element:
            track = track_element.get_text(strip=True)
            if track:
                return track
        
        # Try alternative attribute selectors
        alt_selectors = [
            '.attribute-Track .attribute-value',
            '.attribute-Track span',
            '[data-attribute="Track"]'
        ]
        
        for selector in alt_selectors:
            element = soup.select_one(selector)
            if element:
                track = element.get_text(strip=True)
                if track:
                    return track
        
        # Fallback to general track selectors
        track_selectors = [
            '.track', '.category', '[data-track]'
        ]
        
        for selector in track_selectors:
            element = soup.select_one(selector)
            if element:
                track = element.get_text(strip=True)
                if track:
                    return track
        
        # Try to extract from text patterns
        text = soup.get_text()
        track_patterns = [
            r'Track:\s*([^,\n]+)',
            r'Category:\s*([^,\n]+)'
        ]
        
        for pattern in track_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                track = match.group(1).strip()
                if track:
                    return track
        
        return None
    
    def _extract_session_id_from_text(self, text):
        """Extract session ID from text content"""
        # Look for session ID patterns like AIM357-S, DVT222-S, etc.
        id_patterns = [
            r'\b([A-Z]{3}\d{3}[-\w]*)\b',  # AIM357-S, DVT222-S
            r'Session\s+ID:\s*([A-Z0-9-]+)',
            r'ID:\s*([A-Z0-9-]+)',
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_speakers(self, soup):
        """Extract speaker information"""
        speakers = []
        
        # Try AWS re:Invent specific speaker selectors first
        speaker_elements = soup.select('.mdBtnR-text')
        excluded_terms = ['session full', 'show more', 'collapse', 'expand', 'button']
        
        for element in speaker_elements:
            speaker_name = element.get_text(strip=True)
            if (speaker_name and speaker_name not in speakers and len(speaker_name) > 2 and
                not any(term in speaker_name.lower() for term in excluded_terms)):
                speakers.append(speaker_name)
        
        # Fallback to general speaker selectors
        if not speakers:
            speaker_selectors = [
                '.speaker', '.presenter', '.author', '[data-speaker]'
            ]
            
            for selector in speaker_selectors:
                elements = soup.select(selector)
                for element in elements:
                    speaker = element.get_text(strip=True)
                    if speaker and speaker not in speakers:
                        speakers.append(speaker)
        
        return speakers
    
    def _extract_level(self, soup):
        """Extract session level (Beginner, Intermediate, Advanced)"""
        # Try AWS re:Invent specific attribute selector first
        level_element = soup.select_one('.attribute-Level [data-test="attribute-values"]')
        if level_element:
            level = level_element.get_text(strip=True)
            if level:
                # Extract level from "300 – Advanced" format
                level_match = re.search(r'(Beginner|Intermediate|Advanced|Expert)', level, re.IGNORECASE)
                if level_match:
                    return level_match.group(1).title()
                return level
        
        # Fallback to text patterns
        text = soup.get_text()
        level_patterns = [
            r'(?:Level|Difficulty):\s*(Beginner|Intermediate|Advanced|Expert)',
            r'\b(Beginner|Intermediate|Advanced|Expert)\b'
        ]
        
        for pattern in level_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return None
    
    def _extract_prerequisites(self, soup):
        """Extract prerequisites information"""
        prereq_selectors = [
            '.prerequisites', '.requirements', '[data-prerequisites]'
        ]
        
        for selector in prereq_selectors:
            element = soup.select_one(selector)
            if element:
                prereqs = element.get_text(strip=True)
                if prereqs:
                    return prereqs
        
        return None
    
    def _normalize_time(self, time_str):
        """Normalize time format to HH:MM"""
        try:
            # Remove extra spaces and convert to uppercase
            time_str = re.sub(r'\s+', ' ', time_str.strip().upper())
            
            # Parse 12-hour format
            if 'AM' in time_str or 'PM' in time_str:
                time_obj = datetime.strptime(time_str, '%I:%M %p')
                return time_obj.strftime('%H:%M')
            else:
                # Assume 24-hour format
                time_obj = datetime.strptime(time_str, '%H:%M')
                return time_obj.strftime('%H:%M')
        except:
            return time_str
    
    def _calculate_duration(self, start_time, end_time):
        """Calculate duration in minutes between start and end times"""
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            
            # Handle case where end time is next day
            if end < start:
                end = end.replace(day=end.day + 1)
            
            duration = end - start
            return int(duration.total_seconds() / 60)
        except:
            return None
    
    def _extract_features(self, soup):
        """Extract session features (e.g., Hands-on, Interactive)"""
        features = []
        
        # Try AWS re:Invent specific attribute selector first
        feature_elements = soup.select('.attribute-Features [data-test="attribute-values"]')
        for element in feature_elements:
            feature = element.get_text(strip=True)
            # Clean up comma-separated values and filter out commas and leading commas
            if feature and feature not in features:
                # Remove leading comma and space if present
                clean_feature = feature.lstrip(', ')
                if clean_feature and clean_feature != ',':
                    features.append(clean_feature)
        
        return features
    
    def _extract_topics(self, soup):
        """Extract session topics (e.g., Architecture, Migration & Modernization)"""
        topics = []
        
        # Try AWS re:Invent specific attribute selector first
        topic_elements = soup.select('.attribute-Topic [data-test="attribute-values"]')
        for element in topic_elements:
            topic = element.get_text(strip=True)
            # Clean up comma-separated values and filter out commas and leading commas
            if topic and topic not in topics:
                # Remove leading comma and space if present
                clean_topic = topic.lstrip(', ')
                if clean_topic and clean_topic != ',':
                    topics.append(clean_topic)
        
        return topics
    
    def _extract_roles(self, soup):
        """Extract target roles (e.g., Developer / Engineer, Solution / Systems Architect)"""
        roles = []
        
        # Try AWS re:Invent specific attribute selector first
        role_elements = soup.select('.attribute-Role [data-test="attribute-values"]')
        for element in role_elements:
            role = element.get_text(strip=True)
            # Clean up comma-separated values and filter out commas and leading commas
            if role and role not in roles:
                # Remove leading comma and space if present
                clean_role = role.lstrip(', ')
                if clean_role and clean_role != ',':
                    roles.append(clean_role)
        
        return roles
    
    def _extract_area_of_interest(self, soup):
        """Extract areas of interest (e.g., Innovation & Transformation, Agentic AI)"""
        areas = []
        
        # Try AWS re:Invent specific attribute selector first
        area_elements = soup.select('.attribute-AreaofInterest [data-test="attribute-values"]')
        for element in area_elements:
            area = element.get_text(strip=True)
            # Clean up comma-separated values and filter out commas and leading commas
            if area and area not in areas:
                # Remove leading comma and space if present
                clean_area = area.lstrip(', ')
                if clean_area and clean_area != ',':
                    areas.append(clean_area)
        
        return areas
    
    def _extract_services(self, soup):
        """Extract AWS services mentioned (e.g., Amazon EKS, AWS Lambda)"""
        services = []
        
        # Try AWS re:Invent specific attribute selector first
        service_elements = soup.select('.attribute-Services [data-test="attribute-values"]')
        for element in service_elements:
            service = element.get_text(strip=True)
            # Clean up comma-separated values and filter out commas and leading commas
            if service and service not in services:
                # Remove leading comma and space if present
                clean_service = service.lstrip(', ')
                if clean_service and clean_service != ',':
                    services.append(clean_service)
        
        return services