import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import re
from django.db.models import QuerySet
from django.utils import timezone

from journal.models import Journal
from statistics_and_insights.analytics_utils import JournalAnalytics
from django.conf import settings
from .llm_goal_recommender import generate_with_gemini
from ..models import GoalSuggestion

logger = logging.getLogger(__name__)


@dataclass
class SuggestedGoal:
    title: str
    description: str
    category: Optional[str]
    confidence: float
    source_journal: Optional[Journal]


STOPWORDS = {
    'the','a','an','and','or','but','so','to','of','in','on','for','with','at','by','from','as','is','it','this','that','these','those','i','you','we','they','he','she','my','our','your','their','be','was','were','am','are','been','have','has','had','do','did','does','not','no','yes','very','really','just','too','also','if','then','than','when','while','because','about','into','over','after','before','out','up','down','more','most','less','least','me','him','her','them','us'
}


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    words = re.findall(r"[a-zA-Zà-ÿ0-9']+", text)
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _top_phrases(text: str, max_phrases: int = 5) -> List[Tuple[str, float]]:
    """Extract simple keywords/phrases using unigram+bigram frequency scoring (no external libs)."""
    words = _tokenize(text)
    if not words:
        return []
    # Unigram counts
    counts: Dict[str, int] = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    # Bigram counts
    bigram_counts: Dict[str, int] = {}
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        if words[i] in STOPWORDS or words[i+1] in STOPWORDS:
            continue
        bigram_counts[bigram] = bigram_counts.get(bigram, 0) + 1

    # Combine scores, favor bigrams slightly
    scored: List[Tuple[str, float]] = []
    for k, v in counts.items():
        scored.append((k, float(v)))
    for k, v in bigram_counts.items():
        scored.append((k, float(v) * 1.5))

    # Sort and deduplicate by stem-like starts
    scored.sort(key=lambda t: t[1], reverse=True)
    chosen: List[Tuple[str, float]] = []
    seen_roots: set = set()
    for phrase, score in scored:
        root = phrase.split(' ')[0]
        if root in seen_roots:
            continue
        seen_roots.add(root)
        chosen.append((phrase, score))
        if len(chosen) >= max_phrases:
            break
    return chosen


def _suggestions_from_text(text: str, context_title: Optional[str]) -> List[SuggestedGoal]:
    phrases = _top_phrases(text, max_phrases=5)
    suggestions: List[SuggestedGoal] = []
    for phrase, base_score in phrases:
        title_options = [
            f"Build habit: {phrase}",
            f"Improve {phrase}",
            f"Work on {phrase}",
        ]
        title = title_options[min(len(title_options)-1, 0)]
        context_part = f" '{context_title}'" if context_title else ""
        description = f"Based on your journal{context_part}, focus on {phrase}."
        category = None
        confidence = 0.55 + min(base_score * 0.05, 0.3)  # scale into ~0.55–0.85
        suggestions.append(SuggestedGoal(title, description, category, confidence, None))
    return suggestions


def generate_suggestions_for_user(user, limit: int = 20, max_suggestions: int = 6) -> List[GoalSuggestion]:
    """Lightweight heuristic recommender based on recent journals and simple sentiment.
    Creates GoalSuggestion rows and returns them.
    """
    journals: QuerySet[Journal] = Journal.objects.filter(user=user).order_by('-created_at')[:limit]

    proposed: List[SuggestedGoal] = []
    keyword_counts: Dict[str, int] = {}
    for j in journals:
        try:
            score, sentiment = JournalAnalytics.analyze_sentiment(j.description or '')
            conf_boost = 0.05 if sentiment == 'positive' else (0.0 if sentiment == 'neutral' else -0.05)
            local_suggestions = _suggestions_from_text(j.title + ' ' + (j.description or ''), j.title)
            for s in local_suggestions:
                s.confidence = min(max(s.confidence + conf_boost, 0.0), 0.99)
                s.source_journal = j
                keyword_counts[s.title] = keyword_counts.get(s.title, 0) + 1
            proposed.extend(local_suggestions)
        except Exception as e:
            logger.warning(f"Failed to analyze journal {j.id}: {e}")

    # Simple dedup by title and take top-N by confidence
    unique_by_title = {}
    for s in proposed:
        if s.title not in unique_by_title or s.confidence > unique_by_title[s.title].confidence:
            unique_by_title[s.title] = s
    # Frequency-based confidence bump
    for title, s in unique_by_title.items():
        freq = keyword_counts.get(title, 1)
        s.confidence = min(s.confidence + min(0.15, 0.05 * (freq - 1)), 0.99)

    ranked = sorted(unique_by_title.values(), key=lambda s: s.confidence, reverse=True)[:max_suggestions]

    created_rows: List[GoalSuggestion] = []
    for s in ranked:
        row = GoalSuggestion.objects.create(
            user=user,
            journal=s.source_journal,
            title=s.title,
            description=s.description,
            category=s.category,
            confidence=s.confidence,
            status='pending',
        )
        created_rows.append(row)
    logger.info(f"Generated {len(created_rows)} goal suggestions for user {user}")
    return created_rows


def generate_suggestions_for_journal(user, journal: Journal, max_suggestions: int = 6) -> List[GoalSuggestion]:
    """Generate suggestions focusing on a single journal entry.
    Dedup per (user, journal, title) to avoid duplicates on refresh.
    """
    try:
        text = (journal.title or '') + ' ' + (journal.description or '')
        # Try LLM first if configured
        logger.info(f"[LLM] Attempting LLM suggestions for journal {journal.id}")
        llm_suggestions = []
        try:
            llm_suggestions = generate_with_gemini(journal.title or '', journal.description or '')
        except Exception:
            llm_suggestions = []

        if llm_suggestions:
            created: List[GoalSuggestion] = []
            for g in llm_suggestions:
                exists = GoalSuggestion.objects.filter(
                    user=user, journal=journal, title=g['title']
                ).exists()
                if exists:
                    continue
                row = GoalSuggestion.objects.create(
                    user=user,
                    journal=journal,
                    title=g['title'],
                    description=g.get('description') or '',
                    category=g.get('category'),
                    confidence=g.get('confidence', 0.8),  # use LLM confidence or default
                    status='pending',
                )
                created.append(row)
            if created:
                logger.info(f"[LLM] Generated {len(created)} suggestions for user {user}")
                return created

        # Fallback to local heuristic
        logger.info("[LLM] Falling back to local heuristic suggestions")
        base = _suggestions_from_text(text, journal.title)
        score, sentiment = JournalAnalytics.analyze_sentiment(journal.description or '')
        conf_boost = 0.05 if sentiment == 'positive' else (0.0 if sentiment == 'neutral' else -0.05)
        for s in base:
            s.confidence = min(max(s.confidence + conf_boost, 0.0), 0.99)
            s.source_journal = journal
        # rank and cap
        ranked = sorted(base, key=lambda s: s.confidence, reverse=True)[:max_suggestions]
        created: List[GoalSuggestion] = []
        for s in ranked:
            exists = GoalSuggestion.objects.filter(
                user=user, journal=journal, title=s.title
            ).exists()
            if exists:
                continue
            row = GoalSuggestion.objects.create(
                user=user,
                journal=journal,
                title=s.title,
                description=s.description,
                category=s.category,
                confidence=s.confidence,
                status='pending',
            )
            created.append(row)
        if created:
            logger.info(f"Generated {len(created)} journal-scoped suggestions for user {user}")
        return created
    except Exception as e:
        logger.error(f"Failed to generate suggestions for journal {journal.id}: {e}")
        return []


