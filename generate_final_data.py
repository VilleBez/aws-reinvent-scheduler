#!/usr/bin/env python3
"""
Generate final realistic session data for AWS re:Invent 2025
Focus on Caesars Forum, Venetian, and Wynn venues only
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from processor.keyword_filter import KeywordFilter
from processor.venue_filter import VenueFilter
from processor.session_scorer import SessionScorer
from scheduler.scheduling_algorithm import SchedulingAlgorithm
from output.schedule_formatter import ScheduleFormatter


def generate_realistic_sessions():
    """Generate realistic AWS re:Invent sessions with proper venue filtering"""
    print("🎭 Generating realistic AWS re:Invent 2025 session data...")
    
    sessions = []
    keywords = Config.INTEREST_KEYWORDS
    # Only use the three allowed venues
    venues = Config.ALLOWED_VENUES  # ["Caesars Forum", "Venetian", "Wynn"]
    
    session_types = [
        "Breakout Session", "Workshop", "Chalk Talk", "Builder Session", 
        "Keynote", "Lightning Talk", "Demo", "Hands-on Lab"
    ]
    levels = ["Beginner", "Intermediate", "Advanced"]
    
    # Realistic session title templates
    session_templates = {
        "AI": [
            "Building Production-Ready AI Applications with Amazon Bedrock",
            "Scaling Machine Learning Workloads on Amazon SageMaker",
            "AI-Powered Data Analytics with Amazon Q",
            "Generative AI for Enterprise: Best Practices and Patterns",
            "Computer Vision at Scale with AWS AI Services",
            "Natural Language Processing with Amazon Comprehend",
            "MLOps: Automating Machine Learning Pipelines",
            "AI Ethics and Responsible Machine Learning",
            "Real-time AI Inference with Amazon SageMaker",
            "Building Conversational AI with Amazon Lex"
        ],
        "Kiro": [
            "Accelerate API Development with Kiro CLI",
            "Multi-step Software Development Lifecycle with Kiro",
            "Kiro Best Practices for Enterprise Development",
            "Advanced Kiro Workflows and Automation",
            "Kiro Integration with AWS Services",
            "Building Scalable APIs with Kiro Framework",
            "Kiro Performance Optimization Techniques",
            "Kiro Security and Compliance Patterns",
            "Microservices Architecture with Kiro",
            "Kiro DevOps Integration Strategies"
        ],
        "Architect": [
            "Well-Architected Framework: Security Pillar Deep Dive",
            "Multi-Region Architecture Patterns for Global Applications",
            "Serverless Architecture Best Practices",
            "Microservices Design Patterns on AWS",
            "Event-Driven Architecture with Amazon EventBridge",
            "Cost-Optimized Architecture Design",
            "High-Availability Architecture Patterns",
            "Cloud-Native Application Architecture",
            "Data Architecture for Modern Applications",
            "Security Architecture in the Cloud"
        ],
        "Lakehouse": [
            "Building a Modern Data Lakehouse with AWS",
            "Data Lakehouse Architecture Patterns",
            "Real-time Analytics in the Lakehouse",
            "Data Governance in Lakehouse Environments",
            "Lakehouse Performance Optimization",
            "Machine Learning on Lakehouse Data",
            "Streaming Data into Your Lakehouse",
            "Lakehouse Security and Access Control",
            "Cost Optimization for Data Lakehouses",
            "Migrating to Lakehouse Architecture"
        ],
        "ETL": [
            "Modern ETL Patterns with AWS Glue",
            "Real-time ETL with Amazon Kinesis",
            "Serverless ETL Pipelines",
            "ETL Performance Optimization Strategies",
            "Data Quality in ETL Processes",
            "ETL Monitoring and Observability",
            "Change Data Capture for ETL",
            "ETL Security and Compliance",
            "Cost-Effective ETL Solutions",
            "ETL Testing and Validation"
        ],
        "Trino": [
            "High-Performance Analytics with Trino",
            "Trino Query Optimization Techniques",
            "Scaling Trino for Enterprise Workloads",
            "Trino Security and Access Control",
            "Trino Federation Across Data Sources",
            "Trino Performance Tuning",
            "Trino on Kubernetes Best Practices",
            "Advanced Trino SQL Techniques",
            "Trino Monitoring and Troubleshooting",
            "Trino Cost Optimization Strategies"
        ],
        "DevOps": [
            "CI/CD Best Practices with AWS CodePipeline",
            "Infrastructure as Code with AWS CDK",
            "Container Orchestration with Amazon EKS",
            "DevOps Security: Shifting Left",
            "Monitoring and Observability in DevOps",
            "GitOps Workflows with AWS",
            "Automated Testing in DevOps Pipelines",
            "DevOps Cost Optimization",
            "Multi-Account DevOps Strategies",
            "DevOps Culture and Transformation"
        ]
    }
    
    # Speaker name pools
    first_names = [
        "Sarah", "Michael", "Jennifer", "David", "Lisa", "Robert", "Emily", "James",
        "Maria", "John", "Anna", "Chris", "Jessica", "Daniel", "Amy", "Mark",
        "Laura", "Kevin", "Rachel", "Brian", "Nicole", "Steven", "Michelle", "Paul",
        "Amanda", "Jason", "Stephanie", "Ryan", "Melissa", "Andrew", "Kimberly", "Joshua"
    ]
    
    last_names = [
        "Johnson", "Smith", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore",
        "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson",
        "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker",
        "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez", "Hill"
    ]
    
    # Generate sessions for each conference day
    for day in range(1, 6):  # Dec 1-5, 2025
        date = f"2025-12-0{day}"
        print(f"📅 Generating sessions for {date}...")
        
        # Generate 60-80 sessions per day to ensure enough variety and backups
        num_sessions = random.randint(60, 80)
        
        for i in range(num_sessions):
            # Ensure good keyword distribution
            keyword = keywords[i % len(keywords)]
            
            # Generate realistic session times
            # Conference hours: 8:00 AM - 6:00 PM, avoiding lunch 11:00 AM - 1:00 PM
            available_slots = []
            
            # Morning slots: 8:00 AM - 11:00 AM
            for hour in range(8, 11):
                for minute in [0, 30]:
                    available_slots.append((hour, minute))
            
            # Afternoon slots: 1:00 PM - 6:00 PM
            for hour in range(13, 18):
                for minute in [0, 30]:
                    available_slots.append((hour, minute))
            
            start_hour, start_minute = random.choice(available_slots)
            
            # Session duration (45, 60, or 75 minutes)
            duration = random.choice([45, 60, 75])
            
            start_time = f"{start_hour:02d}:{start_minute:02d}"
            
            # Calculate end time
            total_minutes = start_hour * 60 + start_minute + duration
            end_hour = total_minutes // 60
            end_minute = total_minutes % 60
            end_time = f"{end_hour:02d}:{end_minute:02d}"
            
            # Skip if end time goes beyond 6:30 PM
            if end_hour > 18 or (end_hour == 18 and end_minute > 30):
                continue
            
            # Select session details
            venue = random.choice(venues)
            session_type = random.choice(session_types)
            level = random.choice(levels)
            
            # Create realistic title
            title_templates = session_templates.get(keyword, [f"Advanced {keyword} Strategies"])
            base_title = random.choice(title_templates)
            
            # Add session code
            session_code = f"{keyword[:3].upper()}{random.randint(100, 999)}"
            if random.random() < 0.2:  # 20% chance of sponsored session
                session_code += "-S"
            elif random.random() < 0.3:  # 30% chance of repeat session
                session_code += "-R"
            
            title = f"{base_title} ({session_code})"
            
            # Create realistic description
            descriptions = [
                f"This {session_type.lower()} provides comprehensive insights into {keyword.lower()} technologies and implementation strategies. Learn how to build scalable, secure, and cost-effective solutions using AWS services and {keyword.lower()} best practices.",
                f"Join us for an in-depth exploration of {keyword.lower()} on AWS. This session covers architecture patterns, performance optimization, security considerations, and real-world use cases from enterprise customers.",
                f"Discover how to leverage {keyword.lower()} to accelerate your cloud journey. We'll cover practical implementation strategies, common pitfalls to avoid, and proven patterns for success.",
                f"Learn from AWS experts and customers about {keyword.lower()} best practices. This session includes hands-on demonstrations, architecture deep dives, and actionable takeaways for your organization."
            ]
            description = random.choice(descriptions)
            
            # Generate speakers (1-3 speakers per session)
            num_speakers = random.choices([1, 2, 3], weights=[40, 45, 15])[0]
            speakers = []
            for _ in range(num_speakers):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                title_prefix = random.choice(["", "Dr. ", "Prof. "])
                speaker_name = f"{title_prefix}{first_name} {last_name}"
                speakers.append(speaker_name)
            
            # Generate room assignment
            room_numbers = {
                "Caesars Forum": [f"Forum {i}" for i in range(1, 21)],
                "Venetian": [f"Venetian Ballroom {chr(65+i)}" for i in range(10)] + [f"Level {j} Room {k}" for j in range(2, 5) for k in range(1, 11)],
                "Wynn": [f"Wynn Ballroom {chr(65+i)}" for i in range(8)] + [f"Meeting Room {i}" for i in range(1, 16)]
            }
            room = random.choice(room_numbers[venue])
            
            # Create session object
            session = {
                'session_id': session_code,
                'title': title,
                'description': description,
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration,
                'venue': venue,
                'room': room,
                'session_type': session_type,
                'track': f"{keyword} Track",
                'speakers': speakers,
                'level': level,
                'prerequisites': f"Basic understanding of {keyword.lower()} concepts and AWS services" if level != "Beginner" else None,
                'keywords_matched': [keyword.lower()]
            }
            
            sessions.append(session)
    
    print(f"✅ Generated {len(sessions)} realistic sessions")
    return sessions


def main():
    """Main function to generate final data and schedule"""
    print("🚀 Starting final data generation and scheduling...")
    
    # Generate realistic session data
    sessions = generate_realistic_sessions()
    
    # Save raw sessions
    raw_data_path = os.path.join('data', 'final_raw_sessions.json')
    os.makedirs('data', exist_ok=True)
    
    with open(raw_data_path, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(sessions)} raw sessions to {raw_data_path}")
    
    # Process the sessions
    print("🔄 Processing sessions...")
    
    # Filter by keywords
    keyword_filter = KeywordFilter()
    filtered_sessions = keyword_filter.filter_sessions(sessions)
    print(f"🔍 Filtered to {len(filtered_sessions)} sessions matching keywords")
    
    # Filter by venue (only keep allowed venues)
    venue_filter = VenueFilter()
    venue_filtered_sessions = venue_filter.filter_sessions(filtered_sessions)
    print(f"🏢 Filtered to {len(venue_filtered_sessions)} sessions in allowed venues")
    
    # Score sessions
    scorer = SessionScorer()
    scored_sessions = scorer.score_sessions(venue_filtered_sessions)
    print(f"📊 Scored {len(scored_sessions)} sessions")
    
    # Save processed sessions
    processed_data_path = os.path.join('data', 'final_processed_sessions.json')
    
    with open(processed_data_path, 'w', encoding='utf-8') as f:
        json.dump(scored_sessions, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(scored_sessions)} processed sessions to {processed_data_path}")
    
    # Create schedule
    print("📅 Creating optimized schedule...")
    scheduler = SchedulingAlgorithm()
    schedule = scheduler.create_schedule(scored_sessions, Config.CONFERENCE_DATES)
    
    # Save schedule
    schedule_data_path = os.path.join('data', 'final_schedule.json')
    with open(schedule_data_path, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved schedule to {schedule_data_path}")
    
    # Generate formatted output
    print("📝 Generating formatted output...")
    formatter = ScheduleFormatter()
    
    # Generate markdown output
    markdown_output = formatter.format_schedule(schedule, 'markdown')
    markdown_path = os.path.join('data', 'AWS_reInvent_2025_Schedule.md')
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    # Generate CSV output
    csv_output = formatter.format_schedule(schedule, 'csv')
    csv_path = os.path.join('data', 'AWS_reInvent_2025_Schedule.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_output)
    
    print(f"📄 Generated formatted outputs:")
    print(f"  - {markdown_path}")
    print(f"  - {csv_path}")
    
    # Show statistics
    print("\n📈 Final Statistics:")
    summary = schedule.get('summary', {})
    print(f"  Total conference days: {summary.get('total_conference_days', 0)}")
    print(f"  Total scheduled sessions: {summary.get('total_scheduled_sessions', 0)}")
    print(f"  Total backup sessions: {summary.get('total_backup_sessions', 0)}")
    print(f"  Average session score: {summary.get('average_session_score', 0)}")
    print(f"  Schedule efficiency: {summary.get('schedule_efficiency', 0)} sessions/day")
    
    # Show venue distribution
    venue