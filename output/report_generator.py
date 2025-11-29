"""
Report generator for AWS re:Invent session analysis
"""

from typing import Dict, Any, List
from datetime import datetime


class ReportGenerator:
    def __init__(self):
        self.date_format = '%Y-%m-%d'
    
    def generate_full_report(self, schedule: Dict[str, Any], 
                           all_sessions: List[Dict[str, Any]]) -> str:
        """Generate comprehensive analysis report"""
        report_sections = []
        
        # Title and overview
        report_sections.append("# AWS re:Invent 2025 - Schedule Analysis Report")
        report_sections.append("")
        report_sections.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append("")
        
        # Executive summary
        report_sections.extend(self._generate_executive_summary(schedule, all_sessions))
        
        # Detailed analysis
        report_sections.extend(self._generate_detailed_analysis(schedule, all_sessions))
        
        # Optimization insights
        report_sections.extend(self._generate_optimization_insights(schedule))
        
        # Recommendations
        report_sections.extend(self._generate_recommendations(schedule, all_sessions))
        
        return "\n".join(report_sections)
    
    def _generate_executive_summary(self, schedule: Dict[str, Any], 
                                   all_sessions: List[Dict[str, Any]]) -> List[str]:
        """Generate executive summary section"""
        content = []
        content.append("## 📋 Executive Summary")
        content.append("")
        
        summary = schedule.get('summary', {})
        
        # Key metrics
        total_available = len(all_sessions)
        total_scheduled = summary.get('total_scheduled_sessions', 0)
        total_backups = summary.get('total_backup_sessions', 0)
        avg_score = summary.get('average_session_score', 0)
        
        content.append(f"- **Total Available Sessions**: {total_available}")
        content.append(f"- **Sessions Scheduled**: {total_scheduled} ({(total_scheduled/total_available*100):.1f}% of available)")
        content.append(f"- **Backup Sessions**: {total_backups}")
        content.append(f"- **Average Session Quality**: {avg_score:.2f}/1.00")
        content.append(f"- **Conference Days Covered**: {summary.get('total_conference_days', 0)}")
        content.append("")
        
        # Quality assessment
        if avg_score >= 0.8:
            quality_assessment = "Excellent - High relevance to your interests"
        elif avg_score >= 0.6:
            quality_assessment = "Good - Strong alignment with your keywords"
        elif avg_score >= 0.4:
            quality_assessment = "Fair - Moderate relevance"
        else:
            quality_assessment = "Needs improvement - Consider expanding keyword criteria"
        
        content.append(f"**Quality Assessment**: {quality_assessment}")
        content.append("")
        
        return content
    
    def _generate_detailed_analysis(self, schedule: Dict[str, Any], 
                                   all_sessions: List[Dict[str, Any]]) -> List[str]:
        """Generate detailed analysis section"""
        content = []
        content.append("## 🔍 Detailed Analysis")
        content.append("")
        
        # Daily breakdown
        content.append("### 📅 Daily Breakdown")
        content.append("")
        
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        conference_dates.sort()
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            stats = daily_schedule.get('statistics', {})
            
            try:
                date_obj = datetime.strptime(date, self.date_format)
                formatted_date = date_obj.strftime('%A, %B %d')
            except:
                formatted_date = date
            
            content.append(f"#### {formatted_date}")
            content.append(f"- Sessions: {stats.get('scheduled_sessions', 0)}")
            content.append(f"- Backups: {stats.get('backup_sessions', 0)}")
            content.append(f"- Avg Score: {stats.get('average_score', 0):.2f}")
            
            # Venue distribution for the day
            venue_dist = stats.get('venue_distribution', {})
            if venue_dist:
                venues = [f"{venue} ({count})" for venue, count in venue_dist.items()]
                content.append(f"- Venues: {', '.join(venues)}")
            
            content.append("")
        
        # Keyword analysis
        content.extend(self._analyze_keyword_coverage(schedule))
        
        # Venue analysis
        content.extend(self._analyze_venue_distribution(schedule))
        
        return content
    
    def _analyze_keyword_coverage(self, schedule: Dict[str, Any]) -> List[str]:
        """Analyze keyword coverage across the schedule"""
        content = []
        content.append("### 🎯 Keyword Coverage Analysis")
        content.append("")
        
        summary = schedule.get('summary', {})
        keyword_coverage = summary.get('overall_keyword_coverage', {})
        
        if not keyword_coverage:
            content.append("No keyword coverage data available.")
            content.append("")
            return content
        
        total_sessions = summary.get('total_scheduled_sessions', 0)
        
        content.append("| Keyword | Sessions | Coverage % | Priority |")
        content.append("|---------|----------|------------|----------|")
        
        # Sort by session count
        sorted_keywords = sorted(keyword_coverage.items(), key=lambda x: x[1], reverse=True)
        
        for keyword, count in sorted_keywords:
            coverage_pct = (count / total_sessions * 100) if total_sessions > 0 else 0
            
            # Determine priority based on coverage
            if coverage_pct >= 40:
                priority = "High"
            elif coverage_pct >= 20:
                priority = "Medium"
            else:
                priority = "Low"
            
            content.append(f"| {keyword} | {count} | {coverage_pct:.1f}% | {priority} |")
        
        content.append("")
        
        # Coverage insights
        content.append("**Coverage Insights:**")
        
        high_coverage = [k for k, v in keyword_coverage.items() if v >= total_sessions * 0.4]
        low_coverage = [k for k, v in keyword_coverage.items() if v < total_sessions * 0.2]
        
        if high_coverage:
            content.append(f"- Strong coverage: {', '.join(high_coverage)}")
        
        if low_coverage:
            content.append(f"- Limited coverage: {', '.join(low_coverage)}")
        
        content.append("")
        
        return content
    
    def _analyze_venue_distribution(self, schedule: Dict[str, Any]) -> List[str]:
        """Analyze venue distribution and travel optimization"""
        content = []
        content.append("### 🏢 Venue Distribution Analysis")
        content.append("")
        
        summary = schedule.get('summary', {})
        venue_dist = summary.get('overall_venue_distribution', {})
        
        if not venue_dist:
            content.append("No venue distribution data available.")
            content.append("")
            return content
        
        total_sessions = sum(venue_dist.values())
        
        content.append("| Venue | Sessions | Percentage |")
        content.append("|-------|----------|------------|")
        
        # Sort by session count
        sorted_venues = sorted(venue_dist.items(), key=lambda x: x[1], reverse=True)
        
        for venue, count in sorted_venues:
            percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
            content.append(f"| {venue} | {count} | {percentage:.1f}% |")
        
        content.append("")
        
        # Travel optimization analysis
        content.append("**Travel Optimization:**")
        
        if len(venue_dist) <= 3:
            content.append("- ✅ Good venue concentration - minimal travel required")
        elif len(venue_dist) <= 5:
            content.append("- ⚠️ Moderate venue spread - plan travel routes")
        else:
            content.append("- ❌ High venue spread - consider optimizing for fewer venues")
        
        # Check for venue clustering by day
        content.extend(self._analyze_daily_venue_patterns(schedule))
        
        return content
    
    def _analyze_daily_venue_patterns(self, schedule: Dict[str, Any]) -> List[str]:
        """Analyze venue patterns by day"""
        content = []
        content.append("")
        content.append("**Daily Venue Patterns:**")
        
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        conference_dates.sort()
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            primary_sessions = daily_schedule.get('primary_sessions', [])
            
            if not primary_sessions:
                continue
            
            # Get venues for the day in order
            venues_in_order = []
            for session in sorted(primary_sessions, key=lambda x: x.get('scheduled_start', '00:00')):
                venue = session.get('venue', 'Unknown')
                venues_in_order.append(venue)
            
            # Count venue changes
            venue_changes = 0
            for i in range(len(venues_in_order) - 1):
                if venues_in_order[i] != venues_in_order[i + 1]:
                    venue_changes += 1
            
            try:
                date_obj = datetime.strptime(date, self.date_format)
                formatted_date = date_obj.strftime('%a %m/%d')
            except:
                formatted_date = date
            
            unique_venues = len(set(venues_in_order))
            
            if venue_changes == 0:
                pattern = "✅ Single venue"
            elif venue_changes <= 2:
                pattern = "✅ Minimal travel"
            elif venue_changes <= 4:
                pattern = "⚠️ Moderate travel"
            else:
                pattern = "❌ High travel"
            
            content.append(f"- {formatted_date}: {unique_venues} venues, {venue_changes} changes - {pattern}")
        
        content.append("")
        return content
    
    def _generate_optimization_insights(self, schedule: Dict[str, Any]) -> List[str]:
        """Generate optimization insights"""
        content = []
        content.append("## ⚡ Optimization Insights")
        content.append("")
        
        # Schedule efficiency
        summary = schedule.get('summary', {})
        efficiency = summary.get('schedule_efficiency', 0)
        
        content.append("### 📊 Schedule Efficiency")
        content.append("")
        content.append(f"**Sessions per day**: {efficiency}")
        
        if efficiency >= 6:
            content.append("- ✅ High efficiency - excellent session density")
        elif efficiency >= 4:
            content.append("- ✅ Good efficiency - solid session coverage")
        elif efficiency >= 2:
            content.append("- ⚠️ Moderate efficiency - room for improvement")
        else:
            content.append("- ❌ Low efficiency - consider expanding criteria")
        
        content.append("")
        
        # Time utilization
        content.append("### ⏰ Time Utilization")
        content.append("")
        
        conference_dates = [key for key in schedule.keys() if key != 'summary']
        total_scheduled_hours = 0
        
        for date in conference_dates:
            daily_schedule = schedule[date]
            primary_sessions = daily_schedule.get('primary_sessions', [])
            
            for session in primary_sessions:
                duration = session.get('duration_minutes', 60)  # Default 60 min
                total_scheduled_hours += duration / 60
        
        avg_hours_per_day = total_scheduled_hours / len(conference_dates) if conference_dates else 0
        
        content.append(f"**Average hours per day**: {avg_hours_per_day:.1f}")
        content.append(f"**Total conference hours**: {total_scheduled_hours:.1f}")
        
        if avg_hours_per_day >= 6:
            content.append("- ✅ Intensive schedule - high learning potential")
        elif avg_hours_per_day >= 4:
            content.append("- ✅ Balanced schedule - good mix of learning and networking")
        else:
            content.append("- ⚠️ Light schedule - opportunity for more sessions")
        
        content.append("")
        
        return content
    
    def _generate_recommendations(self, schedule: Dict[str, Any], 
                                 all_sessions: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        content = []
        content.append("## 💡 Recommendations")
        content.append("")
        
        # Schedule optimization recommendations
        content.append("### 🎯 Schedule Optimization")
        content.append("")
        
        summary = schedule.get('summary', {})
        keyword_coverage = summary.get('overall_keyword_coverage', {})
        
        # Keyword balance recommendations
        if keyword_coverage:
            total_sessions = summary.get('total_scheduled_sessions', 0)
            underrepresented = [k for k, v in keyword_coverage.items() if v < total_sessions * 0.15]
            
            if underrepresented:
                content.append(f"- Consider adding more sessions for: {', '.join(underrepresented)}")
        
        # Venue optimization recommendations
        venue_dist = summary.get('overall_venue_distribution', {})
        if len(venue_dist) > 4:
            content.append("- Consider consolidating sessions to fewer venues to reduce travel time")
        
        # Backup session recommendations
        total_backups = summary.get('total_backup_sessions', 0)
        total_scheduled = summary.get('total_scheduled_sessions', 0)
        backup_ratio = total_backups / total_scheduled if total_scheduled > 0 else 0
        
        if backup_ratio < 2:
            content.append("- Consider identifying more backup sessions for flexibility")
        
        content.append("")
        
        # Pre-conference preparation
        content.append("### 📚 Pre-Conference Preparation")
        content.append("")
        content.append("- Download session materials and prerequisites in advance")
        content.append("- Review speaker profiles and company backgrounds")
        content.append("- Plan networking opportunities around your session schedule")
        content.append("- Download venue maps and identify optimal routes")
        content.append("- Set up calendar reminders with 15-minute buffers")
        content.append("")
        
        # During conference tips
        content.append("### 🎪 During Conference")
        content.append("")
        content.append("- Check for last-minute session changes or cancellations")
        content.append("- Use backup sessions if primary sessions are full")
        content.append("- Take notes and photos (where permitted)")
        content.append("- Network during breaks and lunch periods")
        content.append("- Stay hydrated and take breaks between sessions")
        content.append("")
        
        # Post-conference follow-up
        content.append("### 📝 Post-Conference Follow-up")
        content.append("")
        content.append("- Review and organize session notes")
        content.append("- Follow up with speakers and new connections")
        content.append("- Access recorded sessions for missed content")
        content.append("- Share learnings with your team")
        content.append("- Plan implementation of new technologies and practices")
        content.append("")
        
        return content