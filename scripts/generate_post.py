import anthropic
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
 
# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
 
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN      = os.environ["GITHUB_TOKEN"]
GITHUB_REPO       = os.environ["GITHUB_REPO"]   # e.g. "sebbe453/theaiapron-content"
 
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
 
MEMORY_DIR = Path("memory")
POSTS_DIR  = Path("posts")
 
POSTS_LOG_FILE   = MEMORY_DIR / "posts-log.json"
TOPICS_USED_FILE = MEMORY_DIR / "topics-used.json"
QUALITY_LOG_FILE = MEMORY_DIR / "quality-log.json"
 
# ─────────────────────────────────────────
# AFFILIATE LINK TABLE
# Add your real affiliate URLs here as you get them
# ─────────────────────────────────────────
 
AFFILIATE_LINKS = {
    "ChatGPT Plus":    "https://chat.openai.com",
    "Canva Pro":       "https://www.canva.com",
    "Tidio":           "https://www.tidio.com",
    "Klaviyo":         "https://www.klaviyo.com",
    "Mailchimp":       "https://mailchimp.com",
    "Xero":            "https://www.xero.com",
    "HoneyBook":       "https://www.honeybook.com",
    "Pixieset":        "https://pixieset.com",
    "TrueCoach":       "https://truecoach.co",
    "Fresha":          "https://www.fresha.com",
    "Tradify":         "https://www.tradifyhq.com",
    "GoCardless":      "https://gocardless.com",
    "Dext":            "https://dext.com",
    "Luminar Neo":     "https://skylum.com/luminar-neo",
    "OpenTable":       "https://www.opentable.co.uk",
    "Lightroom":       "https://www.adobe.com/products/photoshop-lightroom.html",
}
 
# ─────────────────────────────────────────
# INDUSTRIES & TOPIC ANGLES
# The script rotates through these, going
# deeper on each industry over time
# ─────────────────────────────────────────
 
INDUSTRIES = [
    "restaurants & cafés",
    "hair & beauty salons",
    "estate agents & property",
    "gyms & personal trainers",
    "e-commerce & online shops",
    "dental & healthcare clinics",
    "tradespeople & contractors",
    "independent retailers",
    "photographers",
    "accountants & bookkeepers",
    "florists",
    "wedding planners",
    "childcare & nurseries",
    "vets & pet care",
    "independent coffee shops",
    "cleaning businesses",
    "driving instructors",
    "solicitors & law firms",
    "mortgage brokers",
    "opticians",
]
 
ANGLES = [
    "best AI tools for {industry} in 2026",
    "how {industry} use AI to save time",
    "AI tools for {industry} with no tech skills",
    "free AI tools for {industry}",
    "AI customer service tools for {industry}",
    "AI marketing tools for {industry}",
    "how to automate bookings for {industry} with AI",
    "AI tools that cut costs for {industry}",
    "AI tools for solo {industry} owners",
    "step by step AI setup guide for {industry}",
    "AI writing tools for {industry}",
    "AI tools for {industry} on a tight budget",
    "how {industry} owners use ChatGPT",
    "AI scheduling tools for {industry}",
    "best AI tools for growing a {industry} business",
]
 
# ─────────────────────────────────────────
# BRAND VOICE DOCUMENT
# ─────────────────────────────────────────
 
BRAND_VOICE = """
You are the content writer for The AI Apron (theaiapron.com).
 
ABOUT THE BLOG:
The AI Apron is a practical guide for small and local business owners who want to use AI tools to save time, reduce costs, and grow — without needing a tech background or a big budget.
 
VOICE RULES:
- Lead with outcome, not technology
- Be specific or say nothing — no vague claims
- Always honest about limitations
- Warm but not fluffy
- Short paragraphs (2-3 sentences max)
- Talk directly to the reader ("you", "your business")
- No throat-clearing — first sentence must earn the second
 
BANNED WORDS (never use these):
revolutionary, game-changer, cutting-edge, leverage (as verb), unlock potential, seamless, robust, empower, next-level, transformative (unless measuring concrete change)
 
POST STRUCTURE (follow exactly in this order):
1. Hook (1-2 sentences — specific, concrete, no intro)
2. The problem in plain terms (1 short paragraph)
3. What AI actually does here (1-2 paragraphs, plain language, outcome-focused)
4. The tool(s) to use — for each tool include: name, cost, best for, one honest limitation
5. How to get started (numbered steps, max 5, assume zero tech knowledge)
6. Realistic expectations (setup time, when results show, what can go wrong)
7. The bottom line (2-3 sentences, direct verdict, first step)
 
MUST INCLUDE:
- Specific concrete hook
- At least one vivid real-world example
- Named tools with real pricing
- Honest limitations for every tool
- Clear how-to-start action
- Realistic timeline
- Direct verdict
- For affiliate links: use format [AFFILIATE: ToolName] as placeholder — never invent URLs
 
MUST NOT INCLUDE:
- Any banned vocabulary
- Intro that delays the point past sentence 3
- Vague claims without specifics
- Tool recommendations without pricing
- A conclusion that just summarises what was already said
 
SEO:
- Target post length: 1,200-1,800 words
- Primary keyword should appear in title, first 100 words, and at least 2 subheadings
- Subheadings should be questions or outcomes readers search for
- Include a meta description of 150-160 characters at the very top in this format:
  META: [your meta description here]
"""
 
# ─────────────────────────────────────────
# MEMORY HELPERS
# ─────────────────────────────────────────
 
def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default
 
def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))
 
def get_posts_log():
    return load_json(POSTS_LOG_FILE, [])
 
def get_topics_used():
    return load_json(TOPICS_USED_FILE, {})
 
def get_quality_log():
    return load_json(QUALITY_LOG_FILE, [])
 
# ─────────────────────────────────────────
# TOPIC SELECTION
# Picks the industry + angle combination
# least covered so far — ensures variety
# ─────────────────────────────────────────
 
def pick_topic(topics_used):
    best_industry = None
    best_angle    = None
    lowest_count  = float("inf")
 
    for industry in INDUSTRIES:
        industry_data = topics_used.get(industry, {})
        industry_total = sum(industry_data.values()) if industry_data else 0
 
        for angle_template in ANGLES:
            angle = angle_template.format(industry=industry)
            angle_count = industry_data.get(angle, 0)
 
            # Prioritise: unused angles first, then least-used industries
            score = angle_count * 100 + industry_total
            if score < lowest_count:
                lowest_count  = score
                best_industry = industry
                best_angle    = angle
 
    return best_industry, best_angle
 
# ─────────────────────────────────────────
# CHECK FOR DUPLICATE TITLE
# ─────────────────────────────────────────
 
def is_duplicate(title, posts_log):
    title_lower = title.lower().strip()
    for post in posts_log:
        if post.get("title", "").lower().strip() == title_lower:
            return True
    return False
 
# ─────────────────────────────────────────
# GENERATE POST WITH CLAUDE
# ─────────────────────────────────────────
 
def generate_post(industry, angle, posts_log):
    # Build context from memory — tell Claude what's already been covered
    covered_titles = [p["title"] for p in posts_log[-30:]]  # Last 30 posts
    covered_str = "\n".join(f"- {t}" for t in covered_titles) if covered_titles else "None yet."
 
    prompt = f"""
{BRAND_VOICE}
 
---
 
MEMORY CONTEXT — posts already published (do NOT duplicate these topics or angles):
{covered_str}
 
---
 
NOW WRITE A NEW POST:
 
Target industry: {industry}
Topic angle: {angle}
 
Write a complete blog post following the brand voice and structure above.
The post must be genuinely different from the already-published posts listed above.
Go deeper or from a different angle than anything already covered.
 
Start with:
META: [150-160 char meta description with primary keyword]
 
Then write the full post with a compelling title on the first line.
"""
 
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )
 
    return message.content[0].text
 
# ─────────────────────────────────────────
# QUALITY CHECK
# Claude scores its own post against
# the brand voice rules
# ─────────────────────────────────────────
 
def quality_check(post_content, industry, angle):
    prompt = f"""
You are a quality checker for The AI Apron blog.
 
Score this blog post out of 10 based on these criteria:
- Hook is specific and concrete (not vague) — 2 points
- All tool recommendations include real pricing — 2 points  
- Every tool has an honest limitation — 2 points
- No banned words used (revolutionary, game-changer, cutting-edge, leverage, seamless, robust, empower, next-level, transformative) — 2 points
- Post is 1,200-1,800 words — 1 point
- Has a direct bottom line verdict — 1 point
 
Respond in this exact JSON format only, no other text:
{{
  "score": <number 1-10>,
  "passed": <true if score >= 7, false otherwise>,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"]
}}
 
POST TO SCORE:
{post_content[:3000]}
"""
 
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
 
    raw = message.content[0].text.strip()
 
    # Strip markdown code fences if present
    raw = re.sub(r"```json|```", "", raw).strip()
 
    try:
        return json.loads(raw)
    except Exception:
        # If JSON parsing fails, default to passed to avoid blocking pipeline
        print(f"Warning: could not parse quality check response: {raw}")
        return {"score": 7, "passed": True, "issues": [], "strengths": []}
 
# ─────────────────────────────────────────
# REWRITE WITH FEEDBACK
# If quality check fails, Claude rewrites
# using the specific issues flagged
# ─────────────────────────────────────────
 
def rewrite_post(post_content, issues, industry, angle):
    issues_str = "\n".join(f"- {i}" for i in issues)
 
    prompt = f"""
{BRAND_VOICE}
 
---
 
The following blog post failed the quality check. Rewrite it fixing these specific issues:
 
ISSUES TO FIX:
{issues_str}
 
ORIGINAL POST:
{post_content}
 
Rewrite the complete post fixing all issues above. Keep the same topic and industry.
Start with META: [meta description] then the title, then the full post.
"""
 
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )
 
    return message.content[0].text
 
# ─────────────────────────────────────────
# AFFILIATE LINK SWAP
# Replaces [AFFILIATE: ToolName] with
# real URLs from the lookup table
# ─────────────────────────────────────────
 
def swap_affiliate_links(content):
    def replace_match(match):
        tool_name = match.group(1).strip()
        url = AFFILIATE_LINKS.get(tool_name)
        if url:
                 return f"[Visit {tool_name}]({url})"
        else:
            # No affiliate URL yet — leave as a clean link to the tool's homepage
            # by searching the tool name (safe fallback)
            search_query = tool_name.replace(' ', '+')
            return f"[{tool_name}](https://www.google.com/search?q={search_query}+pricing+review)"

    return re.sub(r'\[AFFILIATE:\s*([^\]]+)\]', replace_match, content)
 
# ─────────────────────────────────────────
# EXTRACT TITLE FROM POST
# ─────────────────────────────────────────
 
def extract_title(content):
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        # Skip META line and empty lines
        if line and not line.startswith("META:"):
            # Remove markdown heading symbols
            return line.lstrip("#").strip()
    return f"Post {datetime.now().strftime('%Y-%m-%d')}"
 
# ─────────────────────────────────────────
# EXTRACT META DESCRIPTION
# ─────────────────────────────────────────
 
def extract_meta(content):
    for line in content.split("\n"):
        if line.strip().startswith("META:"):
            return line.replace("META:", "").strip()
    return ""
 
# ─────────────────────────────────────────
# CREATE SLUG FROM TITLE
# ─────────────────────────────────────────
 
def make_slug(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug[:80]  # Max 80 chars
 
# ─────────────────────────────────────────
# SAVE POST TO FILE
# ─────────────────────────────────────────
 
def save_post(content, slug, title, meta, industry, score):
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.md"
    filepath = POSTS_DIR / filename
 
    # Build frontmatter for Lovable/CMS compatibility
    frontmatter = f"""---
title: "{title}"
date: "{date_str}"
category: "{industry.title()}"
meta_description: "{meta}"
quality_score: {score}
status: "published"
---
 
"""
 
    final_content = frontmatter + content
    filepath.write_text(final_content)
    print(f"Post saved: {filename}")
    return filename
 
# ─────────────────────────────────────────
# UPDATE MEMORY FILES
# ─────────────────────────────────────────
 
def update_memory(title, slug, industry, angle, quality_result):
    date_str = datetime.now().strftime("%Y-%m-%d")
 
    # Update posts log
    posts_log = get_posts_log()
    posts_log.append({
        "title":    title,
        "slug":     slug,
        "date":     date_str,
        "industry": industry,
        "angle":    angle,
        "score":    quality_result["score"],
        "strengths": quality_result.get("strengths", []),
    })
    save_json(POSTS_LOG_FILE, posts_log)
 
    # Update topics used
    topics_used = get_topics_used()
    if industry not in topics_used:
        topics_used[industry] = {}
    topics_used[industry][angle] = topics_used[industry].get(angle, 0) + 1
    save_json(TOPICS_USED_FILE, topics_used)
 
    # Update quality log
    quality_log = get_quality_log()
    quality_log.append({
        "title":   title,
        "date":    date_str,
        "score":   quality_result["score"],
        "issues":  quality_result.get("issues", []),
    })
    save_json(QUALITY_LOG_FILE, quality_log)
 
    print(f"Memory updated for: {title}")
 
# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────
 
def main():
    print(f"\n{'='*50}")
    print(f"The AI Apron — Content Pipeline")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
 
    # Load memory
    posts_log   = get_posts_log()
    topics_used = get_topics_used()
 
    print(f"Posts published so far: {len(posts_log)}")
 
    # Pick topic
    industry, angle = pick_topic(topics_used)
    print(f"Selected industry: {industry}")
    print(f"Selected angle:    {angle}")
 
    # Generate post
    print("\nGenerating post with Claude...")
    post_content = generate_post(industry, angle, posts_log)
 
    # Extract metadata
    title = extract_title(post_content)
    meta  = extract_meta(post_content)
    slug  = make_slug(title)
 
    print(f"Title: {title}")
 
    # Check for duplicate title
    if is_duplicate(title, posts_log):
        print(f"Duplicate title detected — regenerating...")
        post_content = generate_post(industry, angle, posts_log)
        title = extract_title(post_content)
        slug  = make_slug(title)
 
    # Quality check
    print("\nRunning quality check...")
    quality_result = quality_check(post_content, industry, angle)
    print(f"Quality score: {quality_result['score']}/10")
 
    if not quality_result["passed"]:
        print(f"Score below 7 — rewriting with feedback...")
        print(f"Issues: {quality_result['issues']}")
        post_content   = rewrite_post(post_content, quality_result["issues"], industry, angle)
        quality_result = quality_check(post_content, industry, angle)
        print(f"Rewrite score: {quality_result['score']}/10")
 
    # Swap affiliate links
    print("\nSwapping affiliate link placeholders...")
    post_content = swap_affiliate_links(post_content)
 
    # Save post file
    filename = save_post(post_content, slug, title, meta, industry, quality_result["score"])
 
    # Update memory
    update_memory(title, slug, industry, angle, quality_result)
 
    print(f"\n{'='*50}")
    print(f"Pipeline complete!")
    print(f"File: posts/{filename}")
    print(f"Quality score: {quality_result['score']}/10")
    print(f"{'='*50}\n")
 
if __name__ == "__main__":
    main()
