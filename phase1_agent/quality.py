"""
Output validation and quality assurance
Ensures briefing sections are complete and meaningful
"""

from typing import Dict, List, Tuple
from phase1_agent.models import Briefing

class BriefingValidator:
    """Validates briefing completeness and quality"""
    
    # Minimum content requirements
    SECTION_MIN_WORDS = {
        "who_they_are": 20,              # At least 20 words
        "what_they_care_about": 20,      # At least 20 words
        "company_situation": 20,
        "meeting_approach": 20,
        "icebreaker": 10,                # Icebreaker can be shorter
    }
    
    SECTION_MIN_CHARS = {
        "who_they_are": 100,
        "what_they_care_about": 100,
        "company_situation": 100,
        "meeting_approach": 100,
        "icebreaker": 50,
    }
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count meaningful words (exclude common filler)"""
        if not text:
            return 0
        words = text.split()
        # Remove common filler words that inflate counts
        fillers = {"the", "a", "an", "and", "or", "is", "are", "was", "were"}
        meaningful = [w for w in words if w.lower() not in fillers]
        return len(meaningful)
    
    @staticmethod
    def validate_section(name: str, content: str) -> Tuple[bool, str]:
        """
        Validate a single briefing section
        
        Returns: (is_valid, reason)
        """
        if not content or not content.strip():
            return False, f"{name} is empty"
        
        word_count = BriefingValidator.count_words(content)
        char_count = len(content.strip())
        
        min_words = BriefingValidator.SECTION_MIN_WORDS.get(name, 15)
        min_chars = BriefingValidator.SECTION_MIN_CHARS.get(name, 50)
        
        if char_count < min_chars:
            return False, f"{name} too short ({char_count} chars, need {min_chars})"
        
        if word_count < min_words:
            return False, f"{name} too thin ({word_count} meaningful words, need {min_words})"
        
        # Check for placeholder/generic text
        generics = [
            "i don't have access to",
            "i don't have information",
            "unable to determine",
            "not available",
            "unknown"
        ]
        
        if any(generic.lower() in content.lower() for generic in generics):
            return False, f"{name} contains placeholder text"
        
        return True, ""
    
    @staticmethod
    def validate_briefing(briefing: Briefing) -> Tuple[bool, List[str]]:
        """
        Full briefing validation
        
        Returns: (is_valid, list_of_issues)
        """
        if not briefing:
            return False, ["Briefing object is None"]
        
        issues = []
        sections_to_check = [
            ("who_they_are", briefing.who_they_are),
            ("what_they_care_about", briefing.what_they_care_about),
            ("company_situation", briefing.company_situation),
            ("meeting_approach", briefing.meeting_approach),
            ("icebreaker", briefing.icebreaker),
        ]
        
        for section_name, content in sections_to_check:
            is_valid, reason = BriefingValidator.validate_section(section_name, content)
            if not is_valid:
                issues.append(f"✗ {reason}")
        
        # Validate questions
        if not briefing.smart_questions or len(briefing.smart_questions) < 3:
            issues.append(f"✗ Need 3 smart questions, got {len(briefing.smart_questions or [])}")
        else:
            for i, q in enumerate(briefing.smart_questions):
                if not q or len(q) < 10:
                    issues.append(f"✗ Question {i+1} too short or empty")
        
        # Validate avoidances
        if not briefing.things_to_avoid or len(briefing.things_to_avoid) < 2:
            issues.append(f"✗ Need 2 things to avoid, got {len(briefing.things_to_avoid or [])}")
        else:
            for i, avoid in enumerate(briefing.things_to_avoid):
                if not avoid or len(avoid) < 10:
                    issues.append(f"✗ Avoidance {i+1} too short or empty")
        
        # Overall validation
        is_valid = len(issues) == 0
        
        if is_valid:
            print("[VALIDATION] ✓ All sections passed quality checks")
        else:
            print("[VALIDATION] ✗ Found issues:")
            for issue in issues:
                print(f"  {issue}")
        
        return is_valid, issues
    
    @staticmethod
    def get_quality_score(briefing: Briefing) -> float:
        """
        Calculate quality score 0-100 based on content completeness
        
        Used to determine if briefing needs retry
        """
        score = 0.0
        max_score = 100.0
        
        # Base: sections are filled (20 points each)
        sections = [
            briefing.who_they_are,
            briefing.what_they_care_about,
            briefing.company_situation,
            briefing.meeting_approach,
            briefing.icebreaker,
        ]
        
        for section in sections:
            if section and len(section.strip()) > 50:
                score += 20
        
        # Questions complete (10 points)
        if len(briefing.smart_questions or []) >= 3:
            score += 10
        
        # Avoidances complete (10 points)
        if len(briefing.things_to_avoid or []) >= 2:
            score += 10
        
        # Sources available (10 points)
        if len(briefing.sources or []) >= 3:
            score += 10
        
        return min(score, max_score)
    
    @staticmethod
    def should_retry(briefing: Briefing, min_quality: float = 70.0) -> Tuple[bool, str]:
        """
        Determine if briefing quality is too low and should retry
        
        Returns: (should_retry, reason)
        """
        is_valid, issues = BriefingValidator.validate_briefing(briefing)
        
        if is_valid:
            return False, "Briefing passes all validation checks"
        
        quality_score = BriefingValidator.get_quality_score(briefing)
        
        if quality_score < min_quality:
            return True, f"Quality score {quality_score}/100 below threshold {min_quality}"
        
        # Too many critical issues even if score is okay
        critical_issues = [i for i in issues if "empty" in i.lower() or "missing" in i.lower()]
        if len(critical_issues) > 2:
            return True, f"Too many critical issues: {len(critical_issues)}"
        
        return False, "Briefing acceptable despite minor issues"


class BriefingRepair:
    """Attempt to improve low-quality briefings without full retry"""
    
    @staticmethod
    def suggest_improvements(briefing: Briefing, issues: List[str]) -> Dict[str, str]:
        """
        Suggest which sections need improvement
        
        Returns: dict of {section_name: suggestion}
        """
        suggestions = {}
        
        if any("who_they_are" in issue for issue in issues):
            suggestions["who_they_are"] = "Research their background, role, and key achievements"
        
        if any("what_they_care_about" in issue for issue in issues):
            suggestions["what_they_care_about"] = "Look for recent posts, interviews, or announcements"
        
        if any("company_situation" in issue for issue in issues):
            suggestions["company_situation"] = "Search for company news, funding, recent moves"
        
        if any("meeting_approach" in issue for issue in issues):
            suggestions["meeting_approach"] = "Tailor to the context and their interests"
        
        if any("smart_questions" in issue for issue in issues):
            suggestions["questions"] = "Generate specific questions based on research"
        
        return suggestions
