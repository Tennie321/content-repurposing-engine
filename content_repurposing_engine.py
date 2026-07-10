#!/usr/bin/env python3
"""
AI Content Repurposing Engine v1.0
===================================
Transform any piece of content into 8+ platform-optimized formats.

Usage:
  python content_repurposing_engine.py --input article.txt --formats twitter,linkedin
  python content_repurposing_engine.py --interactive
  python content_repurposing_engine.py --demo
  python content_repurposing_engine.py --batch ./content/ --export json

Formats:
  twitter   - Twitter/X thread (max 280 chars/tweet, 25 tweets max)
  linkedin  - LinkedIn post (professional tone, 1500-3000 chars)
  email     - Email newsletter (structured: subject, preview, body, CTA)
  video     - Short-form video script (TikTok/Reels, 30-60 seconds)
  reddit    - Reddit post (story-driven, subreddit-aware)
  instagram - Instagram carousel/caption (hashtag-optimized)
  podcast   - Podcast script (host monologue, 3-5 min)
  summary   - Concise blog summary (executive brief, 200-500 words)

Dependencies: None (Pure Python 3.8+ standard library)
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────
# FORMAT HOOK TEMPLATES
# ─────────────────────────────────────────────────────────

HOOKS = {
    "twitter": [
        "I spent {time_period} testing {topic}. Here's what I learned:",
        "Most people get {topic} wrong. Here's the truth:",
        "Stop doing {bad_thing}. Start doing {good_thing}:",
        "I tried {approach} and the results shocked me:",
        "{number} {topic} lessons that changed everything:",
        "The {topic} strategy that {result} in {time_period}:",
        "I wish someone told me this about {topic} sooner:",
        "Here's exactly how I {action} without {bad_thing}:",
        "Thread: How I went from {start_state} to {end_state} doing {action}:",
        "The #1 mistake in {topic} (and how to fix it):",
    ],
    "linkedin": [
        "I've been thinking about {topic} a lot lately. Here's my take:",
        "After {time_period} of working with {client_type}, I noticed a pattern:",
        "Stop overcomplicating {topic}. Here's the simple truth:",
        "The hardest lesson I learned about {topic}:",
        "I had a conversation with {person_type} that changed my perspective on {topic}:",
        "We're approaching {topic} all wrong. Let me explain:",
        "I used to believe {old_belief}. I was wrong:",
        "Here's a {framework} framework I developed for {topic}:",
        "The gap between {concept_a} and {concept_b} is costing you {cost}:",
        "Real talk about {topic}:",
    ],
    "email": [
        "I found something interesting about {topic}:",
        "Quick insight on {topic} that might change your approach:",
        "You've been thinking about {topic} wrong:",
        "The {topic} playbook that {result}:",
        "Your weekly {topic} tip:",
        "I tested {approach} — here's the data:",
        "This {topic} insight cost me {cost} to learn:",
        "Your {topic} strategy needs one thing:",
        "Can we talk about {topic}?",
        "New research on {topic} you should see:",
    ],
    "video": [
        "You won't believe what happened when I tried {approach}:",
        "This one {topic} hack saves me {cost} every month:",
        "Stop scrolling. This {topic} tip will save you {time_period}:",
        "I was today years old when I learned about {topic}:",
        "Here's why your {topic} strategy isn't working:",
        "The {topic} trick that {number}% of people don't know:",
        "I tried {approach} for {time_period}. Here's what happened:",
        "If you only watch one video about {topic}, watch this:",
        "The easiest {topic} hack you're not using:",
        "I broke {topic} down into {number} simple steps:",
    ],
    "reddit": [
        "I've been doing {topic} for {time_period} and here's what actually works:",
        "Hot take: most {topic} advice is wrong. Here's why:",
        "After spending {cost} on {approach}, I learned one thing:",
        "I tried {approach} for {time_period}. Results inside:",
        "{topic} ruined my {business}. Here's what I'd do differently:",
        "Unpopular opinion about {topic}:",
        "CMV: The way most people approach {topic} is fundamentally broken:",
        "I'm {role} and I finally figured out {topic}. AMA:",
        "My {time_period} experiment with {approach} (data inside):",
        "People who are crushing {topic} — what's your #1 tip?",
    ],
    "instagram": [
        "✨ The {topic} secret nobody talks about ✨",
        "Your daily dose of {topic} wisdom 🧠",
            "This {topic} tip will save you hours:",
        "Stop scrolling and learn this {topic} hack 🔥",
        "I wish I knew this {topic} trick sooner ⏰",
        "The {topic} glow-up formula:",
        "Day {number} of sharing {topic} tips:",
        "POV: You just discovered the best {topic} strategy:",
        "Save this post — it'll transform your {topic} game:",
        "Your reminder that {topic} doesn't have to be hard:",
    ],
    "podcast": [
        "Welcome back to another episode. Today we're tackling {topic}:",
        "Before we dive in, quick story about {topic}:",
        "I want to start with a controversial statement about {topic}:",
        "If you take nothing else from this episode, remember this about {topic}:",
        "Let me tell you why {topic} matters more than ever right now:",
    ],
    "summary": [
        "Key insights on {topic}:",
        "Executive brief: What you need to know about {topic}:",
        "TL;DR — The essential {topic} takeaways:",
    ],
}


# ─────────────────────────────────────────────────────────
# FORMAT TEMPLATES
# ─────────────────────────────────────────────────────────

TWITTER_TEMPLATES = {
    "question": "💡 Question: {question}\n\n{answer}",
    "list": "📋 {number} Key {topic} Insights:\n{items}{cta}",
    "story": "🧵 A short story about {topic}:\n\n{story}\n\nMoral: {lesson}{cta}",
    "how_to": "🔧 How to {goal} in {number} steps:\n{steps}{cta}",
    "data": "📊 The Data on {topic}:\n\n{data_point}\n\nBottom line: {conclusion}{cta}",
    "comparison": "⚖️ {option_a} vs {option_b}: Which is better?\n\n{comparison_points}{cta}",
    "myth": "🚫 Myth: {myth}\n✅ Reality: {reality}\n\n{explanation}{cta}",
    "takeaway": "🎯 The #1 takeaway on {topic}:\n\n{takeaway}{cta}",
}

LINKEDIN_TEMPLATES = {
    "story": """I used to think {old_belief}.

{setup}

Then {inciting_incident}.

{development}

Here's what I learned:

📌 {lesson_1}
📌 {lesson_2}
📌 {lesson_3}

The bottom line: {conclusion}

What's your experience with {topic}? Drop it in the comments 👇""",
    "framework": """I've developed a framework for {topic} that I want to share:

The {framework_name} Framework:

1️⃣ {step_1}
2️⃣ {step_2}
3️⃣ {step_3}
4️⃣ {step_4}
5️⃣ {step_5}

Here's why it works:

{explanation}

Try it this week and let me know how it goes.

Save this post for later 📌""",
    "insight": """I've been thinking about {topic} and here's what I've come to realize:

{main_insight}

{elaboration}

{relevance_to_reader}

What's your take? I'd love to hear different perspectives in the comments.

♻️ Share if you found this valuable""",
}

EMAIL_TEMPLATES = {
    "newsletter": """Subject: {subject_line}
Preview: {preview_text}

Hey {first_name},

{greeting_paragraph}

{main_content}

Here's what stood out to me:

• {point_1}
• {point_2}
• {point_3}

{takeaway}

If you found this useful, share it with someone who needs it.

Best,
{signature_name}

P.S. {ps_line}""",
    "tip": """Subject: {subject_line}

Hi {first_name},

Quick tip on {topic}:

{tip_content}

{elaboration}

Try it out and let me know how it goes.

Cheers,
{signature_name}""",
}

VIDEO_TEMPLATES = {
    "tiktok_style": """[HOOK - 0-3 seconds]
{visual_cue}
{spoken_hook}

[BODY - 3-45 seconds]
{main_points}

[CTA - 45-60 seconds]
{call_to_action}

[TEXT OVERLAY]
{text_overlays}""",
    "educational": """[INTRO - 0-10s]
Hook: {hook}
Titles: {title_overlay}

[BODY - 10-50s]
Key Point 1: {key_point_1}
Key Point 2: {key_point_2}
Key Point 3: {key_point_3}

[OUTRO - 50-60s]
Summary: {summary}
CTA: {call_to_action}
End Screen: {end_screen}""",
}


# ─────────────────────────────────────────────────────────
# CONTENT REPURPOSING ENGINE
# ─────────────────────────────────────────────────────────

class ContentRepurposingEngine:
    """Main engine that repurposes content across formats."""

    def __init__(self, content, title="", source_url=""):
        self.content = content
        self.title = title or "Untitled Content"
        self.source_url = source_url or ""
        self.paragraphs = self._extract_paragraphs(content)
        self.sentences = self._extract_sentences(content)
        self.keywords = self._extract_keywords(content)
        self.stats = self._analyze_content(content)

    def _extract_paragraphs(self, content):
        """Extract non-empty paragraphs from content."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        return paragraphs if paragraphs else [content.strip()]

    def _extract_sentences(self, content):
        """Split content into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', content.replace("\n", " "))
        return [s.strip() for s in sentences if s.strip()]

    def _extract_keywords(self, content):
        """Extract potential keywords (capitalized phrases, key terms)."""
        words = content.lower().split()
        word_freq = {}
        for w in words:
            w = w.strip(".,!?;:\"'()[]{}")
            if len(w) > 3 and w.isalpha():
                word_freq[w] = word_freq.get(w, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
        return [w for w, c in sorted_words[:15]]

    def _analyze_content(self, content):
        """Get content statistics."""
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len(self.sentences)
        paragraph_count = len(self.paragraphs)
        reading_time_min = max(1, round(word_count / 200))
        return {
            "word_count": word_count,
            "char_count": char_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "reading_time_min": reading_time_min,
        }

    def _truncate(self, text, max_len=280, suffix="..."):
        """Truncate text to max_len with suffix."""
        if len(text) <= max_len:
            return text
        return text[:max_len - len(suffix)].rsplit(" ", 1)[0] + suffix

    def _fill_hook(self, template, **kwargs):
        """Fill hook template with available keywords."""
        fallback = {
            "topic": self.keywords[0] if self.keywords else "this strategy",
            "number": str(random.randint(3, 10)),
            "time_period": random.choice([
                "6 months", "a year", "3 months", "the past year", 
                "last quarter", "years", "30 days"
            ]),
            "cost": f"${random.randint(500, 10000)}",
            "result": random.choice([
                "doubled revenue", "saved 20 hours/week", 
                "increased conversions 3x", "cut costs in half"
            ]),
            "action": random.choice([
                "built a system", "automated workflows", 
                "scaled my agency", "generated leads"
            ]),
            "bad_thing": "wasting time on manual work",
            "good_thing": "building automated systems",
            "start_state": "struggling to get clients",
            "end_state": "turning away leads",
            "approach": random.choice([
                "this strategy", "automation", "systematic approach",
                "new methodology"
            ]),
            "client_type": "agency owners",
            "person_type": "a founder",
            "old_belief": "more hours = more results",
            "framework": random.choice(["P.I.P.E.L.I.N.E.", "S.C.A.L.E.", "G.R.O.W.T.H.", "S.Y.S.T.E.M."]),
            "concept_a": "reaction",
            "concept_b": "strategy",
            "role": "an AI automation consultant",
            "business": "business",
            "goal": "grow your business",
        }
        fallback.update(kwargs)
        return template.format(**fallback)

    def _get_hook(self, format_name, **kwargs):
        """Get a random hook for the format."""
        hooks = HOOKS.get(format_name, ["Here's what I learned about {topic}:"])
        hook_template = random.choice(hooks)
        return self._fill_hook(hook_template, **kwargs)

    def _build_cta(self, format_name):
        """Build format-appropriate CTA."""
        ctas = {
            "twitter": random.choice([
                "\n\n💬 What's your take on this?",
                "\n\n👇 Drop your thoughts below",
                "\n\n🔄 RT if you found this useful",
                "\n\nWhich point resonated most?",
            ]),
            "linkedin": "\n\nWhat's been your experience?\n\n♻️ Repost if this was valuable",
            "reddit": "\n\nWhat do you think? Would love to hear your experience.",
        }
        return ctas.get(format_name, "")

    # ─── FORMAT GENERATORS ────────────────

    def to_twitter_thread(self):
        """Convert content to a Twitter/X thread."""
        thread = []
        
        # Hook tweet
        hook = self._get_hook("twitter")
        # Try to relate hook to content
        first_para = self.paragraphs[0][:100] if self.paragraphs else ""
        if len(first_para) > 20:
            hook = self._truncate(first_para, 250)
            hook = hook.rstrip(".,") + ":"
        
        thread.append(hook)

        # Content tweets (break paragraphs into tweet-sized chunks)
        for i, para in enumerate(self.paragraphs):
            sentences = re.split(r'(?<=[.!?])\s+', para)
            current_tweet = ""
            for sentence in sentences:
                if len(current_tweet) + len(sentence) + 3 > 270:
                    if current_tweet:
                        thread.append(current_tweet.strip())
                    current_tweet = sentence + " "
                else:
                    current_tweet += sentence + " "
            if current_tweet.strip():
                thread.append(current_tweet.strip())

        # If content too short, add insights
        if len(thread) < 3:
            insights = []
            for i, kw in enumerate(self.keywords[:5]):
                insights.append(f"{i+1}. {kw.title()} — key insight from this content")
            thread.extend(insights)

        # Add CTA to last tweet
        cta = self._build_cta("twitter")
        if thread:
            thread[-1] = thread[-1] + cta

        # Cap at 25 tweets
        thread = thread[:25]

        return {
            "format": "twitter_thread",
            "tweet_count": len(thread),
            "content": thread,
            "thread_summary": f"🧵 A {len(thread)}-tweet thread based on \"{self.title}\"",
        }

    def to_linkedin_post(self):
        """Convert content to a LinkedIn post."""
        posts = []
        
        # Start with hook/opening
        opening = self._get_hook("linkedin")
        
        # Extract key points from content
        key_points = []
        for s in self.sentences[:6]:
            if len(s) > 50 and len(s) < 300:
                key_points.append(s)
        
        if not key_points:
            key_points = [p[:200] for p in self.paragraphs[:5]]

        # Build body
        body_parts = [opening, ""]

        # Add main content (2-3 paragraphs)
        for p in self.paragraphs[:3]:
            if len(p) > 30:
                body_parts.append(p[:400] + ("..." if len(p) > 400 else ""))
                body_parts.append("")

        # Add key takeaways if we have content
        if len(self.keywords) >= 3:
            body_parts.append("Key takeaways:")
            for kw in self.keywords[:5]:
                body_parts.append(f"• {kw.title()}")
            body_parts.append("")

        # Add engagement question
        body_parts.append("💬 What's been your experience with this?")
        body_parts.append("")
        body_parts.append("♻️ Repost if you found this valuable")
        body_parts.append(f"📌 Follow for more insights on {self.keywords[0] if self.keywords else 'business growth'}")

        post_text = "\n".join(body_parts)

        # LinkedIn limit ~3000 chars
        post_text = self._truncate(post_text, 2900, "...\n\n💬 What's your take?")

        return {
            "format": "linkedin_post",
            "content": post_text,
            "char_count": len(post_text),
        }

    def to_email_newsletter(self):
        """Convert content to an email newsletter."""
        subject = f"Insight: {self.title[:50]}"
        
        preview = self._get_hook("email")
        preview = self._truncate(preview.replace("{topic}", self.keywords[0] if self.keywords else "growth"), 120)

        # Extract key points for bullet list
        bullets = []
        for p in self.paragraphs[:3]:
            s = p[:150].strip()
            if len(s) > 30:
                bullets.append(s)

        # Fill in enough content
        main_content = "\n\n".join(self.paragraphs[:3])
        main_content = self._truncate(main_content, 1500, "...")

        email = f"""Subject: {subject}
From: AI Content Repurposing
Preview: {preview}

Hey there,

I came across something worth sharing on {self.keywords[0] if self.keywords else 'a topic you care about'}.

{main_content}

Here's the key takeaway:
• {bullets[0] if bullets else 'Focus on what works'}
{('• ' + bullets[1]) if len(bullets) > 1 else '• Apply these insights to your workflow'}
{('• ' + bullets[2]) if len(bullets) > 2 else '• Share this with your team'}

If you found value in this, forward it to someone who needs it.

Reply to this email — I read every response.

Best,
AI Content Repurposing Engine

P.S. Save this for later — you'll want to reference it.
"""
        return {
            "format": "email_newsletter",
            "subject": subject,
            "content": email,
            "body_length": len(email),
        }

    def to_video_script(self):
        """Convert content to a short-form video script."""
        hook = self._get_hook("video")
        
        # Extract 3 key points
        points = []
        for p in self.paragraphs[:3]:
            s = p[:200].strip()
            if len(s) > 40:
                points.append(s)

        if len(points) < 3:
            points = [
                f"Point 1 about {self.keywords[0] if self.keywords else 'this topic'}",
                f"Point 2 about {self.keywords[1] if len(self.keywords) > 1 else 'key insights'}",
                f"Point 3: the wrap-up",
            ]

        visual_cues = [
            "Camera: talking head, medium shot",
            "Camera: talking head with B-roll of screens/setup",
            "Camera: close-up with graphics overlay",
            "Camera: medium shot, text-heavy overlay",
        ]

        script = f"""[VIDEO SCRIPT — {self.title}]
Format: Short-form (TikTok/Reels/Shorts)
Target Duration: 45-60 seconds

[HOOK — 0-5s]
Visual: {random.choice(visual_cues)}
Audio: {hook}

[BODY — 5-45s]
Visual: cut to screens/demonstration
Audio: Let me break this down for you.

1. {points[0][:150]}

Visual: text overlay with key stat
Audio: {points[1][:150] if len(points) > 1 else 'Here is the next important point'}

Visual: graphics showing comparison
Audio: And here's the most important part:
{points[2][:150] if len(points) > 2 else 'Apply this to your workflow today'}

[CTA — 45-60s]
Visual: full frame, eye contact
Audio: If you found this helpful, follow for more {', '.join(self.keywords[:2]) if self.keywords else 'actionable insights'} tips.

Text Overlay: FOLLOW FOR MORE 🚀
"""
        return {
            "format": "video_script",
            "content": script,
            "estimated_duration_sec": 60,
        }

    def to_reddit_post(self):
        """Convert content to a Reddit-style post."""
        hook = self._get_hook("reddit")

        # Build story from content
        body_parts = [hook, ""]
        for p in self.paragraphs[:4]:
            body_parts.append(p[:500].strip())
        body_parts.append("")

        # Add takeaways
        body_parts.append("**Key takeaways:**")
        for i, s in enumerate(self.sentences[:4]):
            if len(s) > 30:
                body_parts.append(f"- {s.strip()[:200]}")

        cta = self._build_cta("reddit")
        body_parts.append("")
        body_parts.append(cta)

        return {
            "format": "reddit_post",
            "title": f"I've been working on {self.keywords[0] if self.keywords else 'this'} and here's what I found",
            "content": "\n".join(body_parts),
            "suggested_subreddits": ["r/agency", "r/entrepreneur", "r/smallbusiness", "r/marketing"],
        }

    def to_instagram(self):
        """Convert content to Instagram caption + carousel idea."""
        hook = self._get_hook("instagram")
        
        # Build carousel slides from paragraphs
        carousel = []
        for i, p in enumerate(self.paragraphs[:5]):
            carousel.append({
                "slide": i + 1,
                "text": p[:200].strip() if p else f"Slide {i+1} content",
            })

        # Build caption
        caption_parts = [hook, ""]
        for p in self.paragraphs[:2]:
            caption_parts.append(p[:300].strip())

        # Hashtags
        tags = [f"#{kw.replace(' ', '')}" for kw in self.keywords[:8]]
        tags.extend(["#contentmarketing", "#growth", "#businesstips", "#digitalmarketing"])
        caption_parts.append("")
        caption_parts.append(" ".join(tags))

        return {
            "format": "instagram_post",
            "caption": "\n".join(caption_parts),
            "carousel_slides": len(carousel),
            "hashtag_count": len(tags),
            "carousel_content": carousel,
        }

    def to_podcast_script(self):
        """Convert content to a podcast episode script."""
        hook = self._get_hook("podcast")
        
        bullet_points = []
        for s in self.sentences[:5]:
            if len(s) > 40:
                bullet_points.append(s.strip())

        if len(bullet_points) < 3:
            bullet_points = [f"Key insight about {kw}" for kw in self.keywords[:5]]

        script = f"""PODCAST SCRIPT — "{self.title}"
Estimated duration: 3-5 minutes

[INTRO — 30s]
{self._get_hook("podcast")}

Welcome to another episode. Today we're diving into {self.title}.

[OPENING — 60s]
Let me set the stage:
{hook}

[brief pause]

Here's the context you need:
{bullet_points[0][:200] if bullet_points else 'Context about the topic'}

[BODY — 2-3 min]
Let's dig into the specifics.

Point 1: {bullet_points[1][:300] if len(bullet_points) > 1 else 'First major point'}

Point 2: {bullet_points[2][:300] if len(bullet_points) > 2 else 'Second major point'}

Point 3: {bullet_points[3][:300] if len(bullet_points) > 3 else 'Third major point'}

[WRAP-UP — 30s]
So here's what I want you to take away from this:
{', '.join([bp[:80] for bp in bullet_points[:3]])}

[OUTRO — 15s]
If you enjoyed this episode, share it with someone who needs to hear it. I'll catch you next time.

— End of Episode —
"""
        return {
            "format": "podcast_script",
            "content": script,
            "estimated_duration_min": 4,
        }

    def to_summary(self):
        """Generate a concise content summary."""
        hook = self._get_hook("summary")
        
        # Extract key sentences
        key_sentence = self.sentences[0] if self.sentences else "No content to summarize."
        
        # Build bullet summary
        summary_bullets = []
        for s in self.sentences[:6]:
            if len(s) > 50 and len(s) < 250:
                summary_bullets.append(f"• {s.strip()}")

        if not summary_bullets:
            summary_bullets = [f"• {self.paragraphs[i][:150]}..." for i in range(min(4, len(self.paragraphs)))]

        # Stats
        stats_str = f"📊 {self.stats['word_count']} words · {self.stats['reading_time_min']} min read · {self.stats['sentence_count']} sentences"

        summary = f"""## {self.title}

**TL;DR:** {key_sentence[:250]}

{chr(10).join(summary_bullets[:4])}

{stats_str}
"""
        return {
            "format": "summary",
            "content": summary,
            "word_count": len(summary.split()),
        }

    def generate_all(self):
        """Generate all available formats."""
        return {
            "twitter": self.to_twitter_thread(),
            "linkedin": self.to_linkedin_post(),
            "email": self.to_email_newsletter(),
            "video": self.to_video_script(),
            "reddit": self.to_reddit_post(),
            "instagram": self.to_instagram(),
            "podcast": self.to_podcast_script(),
            "summary": self.to_summary(),
        }

    def generate_formats(self, formats):
        """Generate specific formats."""
        generators = {
            "twitter": self.to_twitter_thread,
            "linkedin": self.to_linkedin_post,
            "email": self.to_email_newsletter,
            "video": self.to_video_script,
            "reddit": self.to_reddit_post,
            "instagram": self.to_instagram,
            "podcast": self.to_podcast_script,
            "summary": self.to_summary,
        }
        results = {}
        for fmt in formats:
            fmt = fmt.strip().lower()
            if fmt in generators:
                results[fmt] = generators[fmt]()
            else:
                results[fmt] = {"error": f"Unknown format: {fmt}. Available: {', '.join(generators.keys())}"}
        return results


# ─────────────────────────────────────────────────────────
# CLI INTERFACE
# ─────────────────────────────────────────────────────────

def format_output(results, output_format="text"):
    """Format results for output."""
    if output_format == "json":
        # Clean up for JSON serialization
        clean = {}
        for fmt, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                if fmt == "twitter":
                    clean[fmt] = {
                        "format": data["format"],
                        "tweet_count": data["tweet_count"],
                        "thread_summary": data["thread_summary"],
                        "tweets": data["content"],
                    }
                else:
                    clean[fmt] = data
        return json.dumps(clean, indent=2)

    # Text output
    lines = []
    for fmt, data in results.items():
        lines.append("=" * 60)
        lines.append(f"📄 FORMAT: {fmt.upper()}")
        lines.append("=" * 60)
        lines.append("")

        if "error" in data:
            lines.append(f"❌ Error: {data['error']}")
            lines.append("")
            continue

        if fmt == "twitter":
            lines.append(f"🧵 Twitter Thread ({data['tweet_count']} tweets)")
            lines.append(data["thread_summary"])
            lines.append("")
            for i, tweet in enumerate(data["content"], 1):
                lines.append(f"  Tweet {i}/{data['tweet_count']}:")
                lines.append(f"  {'─' * 40}")
                lines.append(f"  {tweet}")
                lines.append(f"  {'─' * 40}")
                lines.append("")
        elif fmt == "summary":
            lines.append(data["content"])
        else:
            lines.append(data.get("content", str(data)))
            lines.append("")

        lines.append("")

    return "\n".join(lines)


def interactive_mode():
    """Run interactively — paste content and get repurposed output."""
    print("\n" + "=" * 60)
    print("  AI Content Repurposing Engine — Interactive Mode")
    print("=" * 60)
    print("Paste your content below. Press Ctrl+D (or Ctrl+Z on Windows)")
    print("on a new line when done.")
    print("─" * 60)

    try:
        content_lines = []
        while True:
            line = input()
            content_lines.append(line)
    except EOFError:
        content = "\n".join(content_lines)

    if not content.strip():
        print("\n❌ No content provided. Exiting.")
        return

    print("\n" + "─" * 60)
    title = input("Enter a title for this content (or press Enter for auto-title): ").strip()
    if not title:
        words = content.split()[:5]
        title = " ".join(words) + "..."

    print("\nAvailable formats: twitter, linkedin, email, video, reddit, instagram, podcast, summary")
    formats_input = input("Which formats? (comma-separated, or 'all'): ").strip()
    
    if formats_input.lower() == "all":
        formats = ["twitter", "linkedin", "email", "video", "reddit", "instagram", "podcast", "summary"]
    else:
        formats = [f.strip() for f in formats_input.split(",") if f.strip()]

    print(f"\n🔄 Repurposing into: {', '.join(formats)}...")
    engine = ContentRepurposingEngine(content, title=title)
    results = engine.generate_formats(formats)
    print(format_output(results))


def batch_mode(directory, formats, output_format):
    """Process all text files in a directory."""
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        print(f"❌ Directory not found: {directory}")
        return

    text_files = list(path.glob("*.txt")) + list(path.glob("*.md")) + list(path.glob("*.csv"))
    
    if not text_files:
        print(f"⚠️  No .txt, .md, or .csv files found in {directory}")
        return

    print(f"📁 Processing {len(text_files)} files in {directory}...")

    all_results = {}
    for filepath in text_files:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        title = filepath.stem
        print(f"  → {filepath.name} ({len(content.split())} words)")
        engine = ContentRepurposingEngine(content, title=title)
        all_results[filepath.name] = engine.generate_formats(formats)

    if output_format == "json":
        output_path = path / "repurposed_output.json"
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✅ JSON output saved to: {output_path}")
    elif output_format == "csv":
        csv_path = path / "repurposed_calendar.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Source File", "Format", "Type", "Estimated Output"])
            for filename, formats_data in all_results.items():
                for fmt, data in formats_data.items():
                    if isinstance(data, dict) and "error" not in data:
                        if fmt == "twitter":
                            writer.writerow([filename, fmt, "Thread", f"{data['tweet_count']} tweets"])
                        elif fmt == "summary":
                            writer.writerow([filename, fmt, "Summary", f"{data.get('word_count', 0)} words"])
                        else:
                            content = data.get("content", "")
                            writer.writerow([filename, fmt, "Content", f"{len(content.split())} words"])
        print(f"\n✅ CSV content calendar saved to: {csv_path}")
    else:
        for filename, formats_data in all_results.items():
            print(f"\n{'=' * 60}")
            print(f"📄 {filename}")
            print(f"{'=' * 60}")
            print(format_output(formats_data))


def demo_mode():
    """Run with sample content to demonstrate capabilities."""
    sample_content = """I spent 6 months testing different cold email strategies for my AI automation agency. Here's what actually worked.

The biggest mistake most agencies make is sending generic templates. We tested 47 different email variations across 12 industries and found that personalized subject lines increased open rates by 312%.

Our winning formula: research-first, template-second. Before writing a single word, spend 15 minutes researching the prospect. Check their LinkedIn for recent posts, promotions, or company news. Reference something specific in your first paragraph.

The second breakthrough was timing. Tuesday at 10am had 47% higher response rates than Monday morning. Wednesday afternoon was second best. Friday emails got deleted without being read.

Third discovery: shorter emails win. Emails under 100 words had a 23% reply rate versus 4% for emails over 250 words. Get to the point fast. One insight, one offer, one call to action.

Fourth: follow-ups work but most people give up too early. Our data shows the fourth follow-up email gets the highest conversion rate at 18%. Most people stop after two. The money is in the persistence.

Fifth: case studies outperform feature lists by 3x. Instead of saying 'we do AI automation', say 'we helped a real estate agency save 40 hours per month on lead qualification.' Specific results beat generic claims every time.

We packaged all these findings into a repeatable cold email system that consistently generates 15-20% reply rates for our agency. The system has now been used by 37 different agencies with similar results."""

    engine = ContentRepurposingEngine(
        sample_content,
        title="6 Months of Cold Email Testing: What Actually Works",
        source_url="https://example.com/cold-email-guide"
    )

    print("=" * 60)
    print("  AI Content Repurposing Engine — DEMO MODE")
    print("=" * 60)
    print(f"\n📄 Source: \"{engine.title}\"")
    print(f"📊 Stats: {engine.stats['word_count']} words | {engine.stats['reading_time_min']} min read")
    print("─" * 60)
    print(f"\nGenerating ALL 8 formats...\n")

    results = engine.generate_all()
    text_output = format_output(results)

    print(text_output)
    
    print("─" * 60)
    print("✅ Demo complete! All 8 formats generated.")
    print("Use --interactive to repurpose your own content.")
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="AI Content Repurposing Engine — Transform content into 8+ platform-optimized formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
Examples:
  %(prog)s --input article.txt --formats twitter,linkedin
  %(prog)s --interactive
  %(prog)s --demo
  %(prog)s --batch ./content/ --export json
  %(prog)s --input post.md --formats all --output results.txt

Formats: twitter, linkedin, email, video, reddit, instagram, podcast, summary
        """),
    )

    parser.add_argument("--input", "-i", help="Input file path (text or markdown)")
    parser.add_argument("--title", "-t", help="Content title (auto-detected from file if not provided)")
    parser.add_argument("--formats", "-f", default="all",
        help="Comma-separated formats (default: all). Options: twitter,linkedin,email,video,reddit,instagram,podcast,summary")
    parser.add_argument("--output", "-o", help="Output file path (saves to file instead of stdout)")
    parser.add_argument("--export", "-e", choices=["text", "json"], default="text",
        help="Export format (default: text)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample content")
    parser.add_argument("--batch", help="Batch process all text files in a directory")
    parser.add_argument("--batch-export", choices=["text", "json", "csv"], default="text",
        help="Batch export format (default: text)")

    args = parser.parse_args()

    # Mode: Interactive
    if args.interactive:
        interactive_mode()
        return

    # Mode: Demo
    if args.demo:
        demo_mode()
        return

    # Mode: Batch
    if args.batch:
        formats = ["twitter", "linkedin", "email", "video", "reddit", "instagram", "podcast", "summary"]
        if args.formats.lower() != "all":
            formats = [f.strip() for f in args.formats.split(",")]
        batch_mode(args.batch, formats, args.batch_export)
        return

    # Mode: Single file
    if args.input:
        filepath = Path(args.input)
        if not filepath.exists():
            print(f"❌ File not found: {args.input}")
            sys.exit(1)

        content = filepath.read_text(encoding="utf-8", errors="ignore")
        title = args.title or filepath.stem

        formats = ["twitter", "linkedin", "email", "video", "reddit", "instagram", "podcast", "summary"]
        if args.formats.lower() != "all":
            formats = [f.strip() for f in args.formats.split(",")]

        engine = ContentRepurposingEngine(content, title=title)
        results = engine.generate_formats(formats)
        output = format_output(results, args.export)

        if args.output:
            Path(args.output).write_text(output)
            print(f"✅ Output saved to: {args.output}")
        else:
            print(output)
        return

    # No mode selected
    parser.print_help()
    print("\n\nℹ️  Run with --demo for a demonstration or --interactive to get started.")


if __name__ == "__main__":
    main()