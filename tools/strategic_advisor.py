#!/usr/bin/env python3
"""
Strategic Advisor Tool
Loads business context and matches the question to relevant frameworks.
Outputs a structured brief for Claude to use when answering strategic questions.
"""

import json
import argparse
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
CONTEXT_FILE = TOOLS_DIR / "business_context.json"

# Framework library: keyword triggers → framework details
FRAMEWORKS = [
    {
        "name": "Hormozi Value Equation",
        "source": "Alex Hormozi — $100M Offers",
        "summary": "Value = (Dream Outcome × Perceived Likelihood of Achievement) / (Time Delay × Effort & Sacrifice). To increase perceived value: amplify the dream outcome, boost credibility, reduce time to result, and make it easier. Raising price often increases perceived value if justified.",
        "applies_when": "Pricing, offer design, why people don't buy or churn, low conversion",
        "triggers": ["price", "value", "offer", "conversion", "churn", "cancel", "worth it", "too expensive", "upsell", "upgrade"]
    },
    {
        "name": "Hormozi Lead Engine",
        "source": "Alex Hormozi — $100M Leads",
        "summary": "Four core ways to get leads: Warm Outreach, Post Content, Cold Outreach, Paid Ads. Run all four simultaneously. Owned audience (email, followers) is the highest-leverage asset — it compounds. Affiliates and referrals let other people's audiences work for you.",
        "applies_when": "Acquisition, channel diversification, lead generation, growing subscriber base",
        "triggers": ["lead", "acquisition", "channel", "traffic", "grow", "new customers", "subscribers", "awareness", "audience"]
    },
    {
        "name": "80/20 Principle (Pareto)",
        "source": "Richard Koch — The 80/20 Principle",
        "summary": "80% of results come from 20% of causes. In business: 20% of customers drive 80% of revenue, 20% of products drive 80% of profit, 20% of activities drive 80% of growth. Cut the unproductive 80%, double down on the vital 20%.",
        "applies_when": "Prioritization, resource allocation, product portfolio decisions, customer segmentation",
        "triggers": ["prioritize", "focus", "what to cut", "where to focus", "most important", "highest leverage", "best customers", "which products", "time", "resources"]
    },
    {
        "name": "Jobs-to-be-Done (JTBD)",
        "source": "Clayton Christensen — Competing Against Luck",
        "summary": "Customers 'hire' your product to do a job — functional, emotional, or social. When the job is done poorly, or a better solution appears, they 'fire' you. Understand what job parents are hiring the subscription to do (and what makes them fire it). The job is often emotional: 'I feel like a better parent.'",
        "applies_when": "Churn, messaging, positioning, product development, retention",
        "triggers": ["why", "churn", "cancel", "retention", "messaging", "positioning", "what do customers want", "understand", "motivation"]
    },
    {
        "name": "LTV:CAC Unit Economics",
        "source": "SaaS / DTC growth fundamentals",
        "summary": "Healthy LTV:CAC = 3:1+. At 1.56x, every dollar spent acquiring customers returns only $1.56 — margins are consumed before payback. Fix by: (1) increasing LTV via reduced churn or upsells, (2) reducing CAC via owned/organic channels, or (3) both. Never scale paid acquisition until LTV:CAC > 3:1.",
        "applies_when": "Profitability, scaling, paid ad strategy, subscription economics",
        "triggers": ["ltv", "cac", "unit economics", "profitable", "profitability", "scale", "ads", "return on ad spend", "roas", "payback", "margin"]
    },
    {
        "name": "Time to Value (TTV)",
        "source": "Product-led growth / SaaS retention",
        "summary": "The faster a subscriber experiences the core value, the higher retention. For this subscription, the core value is the parenting coach and transformation (feeling more confident as a parent). If a member doesn't use the coach or access a key resource in the first 7 days (during trial), they will not convert or will churn quickly. Onboarding should aggressively drive toward one 'aha moment.'",
        "applies_when": "Trial conversion, subscription churn, onboarding, retention",
        "triggers": ["trial", "onboarding", "first week", "new member", "activation", "aha moment", "engage", "usage", "retention", "churn"]
    },
    {
        "name": "Habit Loop",
        "source": "Nir Eyal — Hooked",
        "summary": "Products that become habits have a loop: Trigger → Action → Variable Reward → Investment. For subscription retention: create external triggers (weekly email nudge, coach reminder), reduce friction to action (easy to book a call, one-click resource access), deliver variable rewards (new content, coach insight), and get investment (journaling, progress tracking). Habit = retention.",
        "applies_when": "Subscription engagement, churn reduction, product design",
        "triggers": ["habit", "engagement", "sticky", "retention", "churn", "members not using", "inactive", "usage"]
    },
    {
        "name": "Cialdini's Principles of Influence",
        "source": "Robert Cialdini — Influence",
        "summary": "Six principles: (1) Reciprocity — give first (lead magnets already doing this), (2) Commitment/Consistency — small yes leads to bigger yes, (3) Social Proof — testimonials, member count, success stories, (4) Authority — certified coach, expert credentials, (5) Liking — relatable brand personality, (6) Scarcity/Urgency — limited trial slots, cohort enrollment. Apply across checkout, onboarding, and retention.",
        "applies_when": "Conversion, copywriting, offers, subscription sales, retention",
        "triggers": ["conversion", "copy", "messaging", "sell", "persuade", "trust", "testimonial", "social proof", "urgency", "scarcity"]
    },
    {
        "name": "Revenue per Subscriber Economics",
        "source": "Subscription business fundamentals",
        "summary": "At $75/quarter ($25/month) with a certified coach offering 1:1 calls, this subscription is likely underpriced. Hormozi would say: the dream outcome (becoming a confident, effective parent) is worth far more than $25/month. Underpricing can signal low value. Consider: testing a price increase, adding tiers (coach-included vs self-serve), or repositioning the coach access as a premium add-on.",
        "applies_when": "Pricing strategy, subscription growth, revenue per subscriber",
        "triggers": ["pricing", "price", "tier", "plan", "increase", "revenue", "subscription revenue", "arpu"]
    },
    {
        "name": "Owned Media vs Rented Media",
        "source": "Content marketing / digital strategy fundamentals",
        "summary": "Rented media (Meta, TikTok, Amazon) can be taken away, algorithmically suppressed, or become more expensive. Owned media (email list, SMS, community) compounds over time with no incremental cost. A 600k email list with 50%+ open rate is more valuable than any ad account. Every strategy should be pushing people onto owned media.",
        "applies_when": "Channel strategy, reducing Meta dependency, growing owned audience",
        "triggers": ["channel", "meta", "tiktok", "amazon", "platform risk", "algorithm", "email", "own", "dependency", "diversify"]
    },
    {
        "name": "Segmentation & ICP Focus",
        "source": "Geoffrey Moore — Crossing the Chasm / general marketing",
        "summary": "Not all customers are equal. Professionals (low churn, $297/year) are a fundamentally better customer than churning parents. Applying 80/20: focus acquisition, onboarding, and product development on your best-performing segment first. Don't serve everyone equally — serve your best customer exceptionally.",
        "applies_when": "Customer segmentation, ICP definition, resource allocation, B2B vs B2C strategy",
        "triggers": ["segment", "icp", "ideal customer", "professional", "b2b", "school", "therapist", "educator", "focus", "target"]
    },
    {
        "name": "Referral & Word-of-Mouth Engine",
        "source": "Jonah Berger — Contagious / growth marketing",
        "summary": "Parenting and education are high word-of-mouth categories — people naturally share what helps their kids. A referral program converts satisfied members into acquisition channels at near-zero CAC. Structure: give a free month for every referral who subscribes. Expected result: reduces blended CAC, increases LTV (referred customers churn less), and creates community.",
        "applies_when": "Reducing CAC, growing subscription without paid ads, community building",
        "triggers": ["referral", "word of mouth", "viral", "share", "community", "affiliate", "partner", "refer a friend"]
    },
    {
        "name": "B2B / Institutional Sales",
        "source": "Strategic sales fundamentals",
        "summary": "A school district or therapy practice signing up 50 professionals is worth $14,850/year ($297 × 50) from one deal. Institutional sales require: a case study or pilot program, a dedicated proposal/pricing page, and a champion inside the organization. Even 10 institutional accounts at 20 seats = $59,400/year. One salesperson doing this full-time can dramatically shift the revenue mix.",
        "applies_when": "B2B sales, professional segment expansion, revenue diversification",
        "triggers": ["school", "district", "institution", "b2b", "enterprise", "group", "team", "bulk", "organization", "professional"]
    },
    {
        "name": "Email Monetization",
        "source": "Email marketing best practices / DTC playbook",
        "summary": "600k subscribers at 50%+ open rates = 300k people reading every email. At industry avg $1-2 revenue per subscriber per month from email, this list should generate $600k-$1.2M/month in attributable revenue. If it's only generating a fraction of that, the gap is in: (1) frequency, (2) segmentation, (3) offer relevance, or (4) the subscription CTA. This list is the biggest untapped lever in the business.",
        "applies_when": "Revenue growth, subscription conversion, channel diversification",
        "triggers": ["email", "list", "newsletter", "campaign", "sequence", "nurture", "monetize", "convert"]
    },
    {
        "name": "The Flywheel (vs Funnel Thinking)",
        "source": "Jim Collins — Good to Great / HubSpot flywheel",
        "summary": "A funnel loses energy at each stage. A flywheel uses each output as input to the next cycle. For this business: Physical product buyer → email subscriber → subscription member → refers a friend → new buyer. Each stage should feed the next. Currently, most physical buyers never become subscribers. Fixing the funnel-to-flywheel conversion is the structural growth lever.",
        "applies_when": "Growth strategy, customer journey, retention, business model",
        "triggers": ["growth", "scale", "strategy", "model", "flywheel", "journey", "lifecycle", "repeat", "retention", "compound"]
    }
]


def match_frameworks(question: str) -> list[dict]:
    """Return frameworks most relevant to the question based on keyword matching."""
    question_lower = question.lower()
    scored = []
    for fw in FRAMEWORKS:
        score = sum(1 for trigger in fw["triggers"] if trigger in question_lower)
        if score > 0:
            scored.append((score, fw))
    scored.sort(key=lambda x: x[0], reverse=True)
    matched = [fw for _, fw in scored[:4]]
    # Always include LTV:CAC if fewer than 2 matched (it's almost always relevant)
    if len(matched) < 2:
        ltv_fw = next((fw for fw in FRAMEWORKS if fw["name"] == "LTV:CAC Unit Economics"), None)
        if ltv_fw and ltv_fw not in matched:
            matched.append(ltv_fw)
    return matched


def load_business_context() -> dict:
    if not CONTEXT_FILE.exists():
        print(f"ERROR: business_context.json not found at {CONTEXT_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(CONTEXT_FILE) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Strategic Advisor — business context + framework matcher")
    parser.add_argument("--question", "-q", required=True, help="The strategic question to analyze")
    args = parser.parse_args()

    context = load_business_context()
    frameworks = match_frameworks(args.question)

    output = {
        "question": args.question,
        "business_snapshot": {
            "mission": context["company"]["brand_mission"],
            "revenue": context["metrics"]["revenue_last_year"],
            "goal": f"{context['metrics']['revenue_goal']} at {context['metrics']['profitability_goal']} profitability",
            "ltv_cac": f"{context['metrics']['ltv_cac_ratio']}x (benchmark: {context['metrics']['healthy_ltv_cac_benchmark']}x)",
            "owned_audience": f"{context['owned_audience']['email_list']} email ({context['owned_audience']['email_open_rate']} open rate), {context['owned_audience']['social_following']} social",
            "subscription_status": f"~{context['products']['subscription']['active_subscribers_estimate']} active subscribers — {context['products']['subscription']['churn_profile']['parents']}",
            "top_challenges": context["strategic_challenges"][:4],
            "top_opportunities": context["strategic_opportunities"][:4]
        },
        "relevant_frameworks": frameworks,
        "instruction": "Use the business snapshot and frameworks above to give a specific, actionable strategic answer. Reference the real numbers. Name the frameworks being applied. Keep it practical — what should they actually do, in what order, and why."
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
