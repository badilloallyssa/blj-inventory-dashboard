# Skill: Strategic Advisor

## Objective
Answer strategic questions about the business using a combination of the stored business context and proven marketing/business frameworks. Deliver specific, actionable advice grounded in real numbers — not generic consulting language.

## Trigger
Use this skill whenever the user asks a question about:
- Business strategy or growth
- Marketing, acquisition, or channel decisions
- Subscription, retention, or churn
- Pricing, offers, or product decisions
- Profitability, unit economics, or scaling
- Prioritization of initiatives
- Hiring, operations, or resource allocation
- Competitive positioning

When in doubt, run the tool — having the business context in front of you always improves the answer.

## Required Inputs
- User's question (required)
- No other inputs needed — context is stored in `tools/business_context.json`

## Steps

### Step 1: Run the tool
```bash
python tools/strategic_advisor.py --question "paste the question here"
```

This returns:
- `business_snapshot` — key metrics and context
- `relevant_frameworks` — 2-4 frameworks matched to the question
- `top_challenges` and `top_opportunities`

### Step 2: Structure the answer

Always follow this structure:

**1. Bottom line first**
One sentence: what's the core strategic answer or recommendation?

**2. Why (grounded in the business context)**
Use real numbers from the business snapshot. Example: "With LTV:CAC at 1.56x and 600k emails at 50% open rate, the fastest path isn't more ads — it's converting the audience you already have."

**3. Framework(s) applied**
Name 1-3 frameworks and explain how they apply. Example:
- *Hormozi Value Equation*: The subscription is underpriced relative to the outcome (1:1 coaching + resources for $25/month). Price and perceived value are misaligned.
- *Time to Value*: 7-day trial is too short for a coaching relationship to form. Members need to experience one coaching session before trial ends.

**4. What to do — in order**
Give 3-5 specific actions, ranked by leverage. Use numbers wherever possible. Avoid vague advice like "improve onboarding" — say "add a mandatory coach intro call within the first 3 days of trial."

**5. What to avoid**
Flag any traps or common mistakes that apply here.

## Communication Rules
- Always explain simply — plain language, short sentences, concrete examples
- No jargon unless already established with the user
- If a concept has math, show a worked example with real numbers from the business
- Lead with the answer, not the framework
- Be direct — if something is a mistake, say so

## Framework Library Reference

The tool will surface the most relevant frameworks, but here's the full list available:

| Framework | Source | Best For |
|---|---|---|
| Hormozi Value Equation | $100M Offers | Pricing, offer design, churn |
| Hormozi Lead Engine | $100M Leads | Acquisition, channel strategy |
| 80/20 Principle | Richard Koch | Prioritization, focus |
| Jobs-to-be-Done | Christensen | Churn, messaging, product |
| LTV:CAC Unit Economics | SaaS/DTC fundamentals | Profitability, scaling |
| Time to Value (TTV) | PLG / SaaS retention | Trial conversion, onboarding |
| Habit Loop | Nir Eyal — Hooked | Engagement, sticky products |
| Cialdini's Influence | Robert Cialdini | Conversion, copywriting |
| Revenue per Subscriber | Subscription fundamentals | Pricing, ARPU |
| Owned vs Rented Media | Content/digital strategy | Channel risk, email strategy |
| Segmentation & ICP Focus | Crossing the Chasm | Customer focus, B2B vs B2C |
| Referral & Word-of-Mouth | Jonah Berger — Contagious | Low-CAC growth |
| B2B / Institutional Sales | Strategic sales | Professional expansion |
| Email Monetization | DTC email playbook | Owned channel revenue |
| The Flywheel | Jim Collins | Growth model, lifecycle |

## Business Context Quick Reference

Key facts always worth knowing:
- **Revenue**: $8M last year → target $11M at 15% profitability
- **LTV:CAC**: 1.56x (target: 3.0x+) — this is the core constraint on growth
- **Email list**: 600k subscribers at 50%+ open rates — massively underutilized
- **Social**: 2M followers (Instagram dominant)
- **Subscription**: ~500-1,500 active subscribers — tiny relative to audience
- **Subscription churn**: Parents churn, professionals don't
- **Professional pricing**: $297/year (low churn, underexploited)
- **Primary channel**: Meta/TikTok paid ads (concentration risk)
- **Amazon**: Meaningful but correlated with Meta (double concentration)
- **What hasn't worked**: Influencer marketing, PostPilot direct mail

## Edge Cases

**If the question is too broad** (e.g., "how do I grow?"):
Run the tool, then structure the answer around the top 3 strategic opportunities from the context file. Help them prioritize rather than answering everything.

**If the question requires data we don't have** (e.g., "what's our trial conversion rate?"):
Answer the strategic question directionally, then flag what data they should go collect to make a better decision.

**If the question is about an experiment or test**:
Use the Lean/MVP framing — what's the minimum test to validate the hypothesis before committing resources?

**If asked about a competitor**:
Default to the fragmented market context — no dominant player. Advice: own a niche completely before expanding, not the reverse.

## Output Format
- Plain prose with **bold section headers**
- Use bullet points for action lists
- Include numbers wherever they exist
- Keep total response under ~400 words unless complexity requires more
- End with a "Watch out for" or "Biggest risk" note when relevant

## Updating This Skill
If you discover new patterns, constraints, or better approaches:
- Update `tools/business_context.json` with new metrics or context when the user shares them
- Add new frameworks to the FRAMEWORKS list in `tools/strategic_advisor.py`
- Do not overwrite this skill file without asking — these instructions are preserved and refined over time
