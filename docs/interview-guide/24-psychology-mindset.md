# 24 — Interview Psychology & Mindset

> This file is about HOW to think during the interview — not what to say, but how to NEVER go wrong.

---

## THE 5 RULES THAT PREVENT FAILURE

### Rule 1: Never Say "I Don't Know" Empty-Handed

**Wrong**: "I don't know what Apache Flink is."

**Right**: "I haven't worked with Flink directly, but I know it's a stream processing framework similar to Spark Structured Streaming, which I've used in my Nova project for Kafka event ingestion. From what I understand, Flink has lower latency for true event-at-a-time processing, while Spark Structured Streaming works in micro-batches. I'd be excited to learn it."

**Pattern**: "I haven't used X, but I know Y (similar thing I've used), and the difference is Z. I'd be excited to learn it."

This shows: honesty + related knowledge + learning attitude.

---

### Rule 2: Always Mention What You REJECTED and WHY

**Wrong**: "I used XGBoost."

**Right**: "I chose XGBoost over Random Forest and neural networks. Random Forest was close, but XGBoost handles class imbalance natively with scale_pos_weight. Neural networks would overfit on 253K tabular records — the Grinsztajn 2022 benchmark showed tree-based models outperform deep learning on tabular data."

Let's unpack every term in that answer so you UNDERSTAND it and can explain further if asked:

- **XGBoost (eXtreme Gradient Boosting)**: An algorithm that trains hundreds of small decision trees one after another. Each new tree focuses on correcting the mistakes of the previous trees. Like a team of weak learners that together become strong. It's the go-to for tabular (spreadsheet-like) data.

- **Random Forest**: Also uses decision trees, but trains them ALL independently in parallel (not sequentially like XGBoost). Each tree votes, majority wins. Simpler but doesn't have a built-in way to handle imbalanced data.

- **Class imbalance**: When one category vastly outnumbers the other. In your diabetes data, 86% of patients are healthy, only 14% are diabetic. The model gets lazy — it learns that predicting "healthy" every time gives 86% accuracy. It catches ZERO diabetic patients. 86% accuracy but completely useless.

- **scale_pos_weight=6.16**: Tells XGBoost "missing a diabetic patient is 6.16x worse than a false alarm on a healthy patient." Calculated as: 218,334 healthy / 35,346 diabetic = 6.16. Now the model is FORCED to learn patterns that catch diabetic patients, because missing them costs 6x more during training.

- **Overfit**: When a model memorizes the training data instead of learning real patterns. It scores 99% on training data but fails on new data. Like a student who memorizes exam answers but can't solve new problems. Neural networks with limited data (253K is "limited" for deep learning) tend to overfit on tabular data.

- **Tabular data**: Data in rows and columns — like a spreadsheet or SQL table. Your health data is tabular: each row is a patient, each column is a measurement (BMI, age, blood pressure). This is different from images or text, where neural networks excel.

- **Grinsztajn 2022**: A NeurIPS research paper that benchmarked tree-based models (XGBoost, Random Forest) against deep learning on 45 tabular datasets. Result: tree models won on medium-sized tabular data. This is your academic backing for choosing XGBoost.

**Pattern**: "I chose X over Y and Z because [specific technical reason]."

This shows: you evaluated options, you have depth, you make informed decisions.

---

### Rule 3: Always Give NUMBERS

**Wrong**: "I improved the pipeline."

**Right**: "I improved Spark execution time by 30% — from 45 minutes to 31 minutes — through broadcast joins on dimension tables under 100MB, partition pruning on trade_date, and predicate pushdown to the Parquet reader."

**Pattern**: [What] + [Number] + [How]

Interviewers remember numbers. "30% improvement" sticks in their head during the hiring committee meeting.

---

### Rule 4: Always Discuss FAILURE MODES

**Wrong**: "The prediction API returns the result."

**Right**: "The prediction API returns the result. If the model isn't loaded, it returns 503. If the input is invalid, Pydantic returns 422 with the specific field error. If there's an unexpected exception, the middleware catches it and returns a UUID error ID — never a stack trace — for debugging without exposing PII."

**Pattern**: "Here's what happens when it works. Here's what happens when it BREAKS."

This shows: production thinking. Junior engineers only think about the happy path.

---

### Rule 5: End Every Answer With a Forward Look

**Wrong**: "That's how I did it."

**Right**: "That's how I did it. If I were to improve this, I'd add SHAP explainability to show which features contributed most to each prediction, and implement model drift monitoring with Evidently AI."

**Pattern**: "Here's what I did. Here's what I'd do NEXT."

This shows: growth mindset, you're always thinking ahead.

---

## TRAPS AND HOW TO AVOID THEM

### Trap 1: "Rate yourself 1-10 on Python"

**The trap**: Say 9 or 10 → they'll ask obscure questions to humiliate you. Say 5 → you look weak.

**The answer**: "I'd say 7-8. I use Python daily for ETL, API development, and ML. I'm very comfortable with pandas, PySpark, FastAPI, and data processing patterns. I know there's always more to learn — for example, I'd like to deepen my knowledge of async patterns and metaclasses."

**Rule**: Never above 8. Always mention what you still want to learn.

---

### Trap 2: "What's your biggest weakness?"

**The trap**: Say a real weakness → they worry. Say "I work too hard" → they know you're lying.

**The answer**: "I tend to over-engineer solutions initially. In my Healthcare project, I built 7 middleware layers and comprehensive testing when a simpler MVP might have shipped faster. I've learned to ask 'what's the minimum viable solution?' first, then iterate. I now use a 'make it work, make it right, make it fast' approach."

**Rule**: Pick a REAL weakness that shows you're an engineer who cares about quality, then show how you're fixing it.

---

### Trap 3: "Why are you leaving TCS?"

**The trap**: If you criticize TCS → red flag. If you sound desperate → red flag.

**The answer**: "TCS gave me a strong foundation — Spark, SQL, production systems, working with large enterprises like Nomura. I'm now looking for a role where I can (1) work on more modern data stacks, (2) get closer to the AI/ML side of data engineering, and (3) be in an environment that prioritizes engineering growth."

**Rule**: Appreciate current employer + frame the move as growth, not escape.

---

### Trap 4: "Do you have any questions?" (saying "No")

**The trap**: Saying "no" signals disinterest.

**Always ask at least 3:**
1. "What does the data stack look like here?" (shows technical interest)
2. "What's the biggest engineering challenge the team is facing?" (shows you want to solve problems)
3. "How does career growth work for data engineers here?" (shows you're thinking long-term)

**Bonus power questions:**
- "How does your team handle data quality in production?"
- "Is there a culture of code reviews and knowledge sharing?"
- "What does on-call look like for this team?"

---

### Trap 5: "Can you start immediately?"

**The trap**: Saying yes might signal desperation. Being rigid might lose the offer.

**The answer**: "I have a [30-day/60-day] notice period at TCS. I'll work with my manager to see if we can expedite it. I'd like to wrap up my current responsibilities properly — that's the same professionalism I'd bring to your team."

---

### Trap 6: "What if the interviewer is wrong about something?"

**The approach**: NEVER say "you're wrong." Instead:

**Wrong**: "No, that's not how Spark works."

**Right**: "That's interesting — in my experience with Spark at Nomura, I've seen it work differently. The shuffle happens when... but I could be thinking of a different context. Could you tell me more about the scenario you're describing?"

**Rule**: Disagree by sharing your experience, not by correcting them. Then ask them to elaborate.

---

## BODY LANGUAGE & COMMUNICATION

### Before the Interview
- Sleep well. Seriously. Your brain processes patterns during sleep.
- Have water nearby. Sipping water buys thinking time.
- Have your resume printed in front of you (even for virtual interviews).
- Open your projects in the browser — ready to screenshare.

### During the Interview
- **Pause before answering**. 3 seconds of thinking looks confident. Rushing looks nervous.
- **Think out loud** during coding. "I'm thinking about using a hash map here because lookup is O(1)..."
- **Ask clarifying questions** before jumping into coding. "Should I handle edge cases like empty input?"
- **Say "Let me think about this"** — it's NEVER a bad thing to say.

### When Stuck
- "I'm not sure about the exact syntax, but the approach would be..."
- "I haven't encountered this specific scenario, but here's how I'd reason through it..."
- "Can I talk through my thought process? I think the key insight is..."

### Virtual Interview Specifics
- Camera ON, good lighting, clean background
- Look at the CAMERA when speaking (not the screen) — appears as eye contact
- Mute when not speaking to avoid background noise
- Have a code editor ready (VS Code) for live coding

---

## SALARY NEGOTIATION

### When They Ask "What are your expectations?"

**Never give a number first.** Always try:
> "I'm flexible on compensation. Could you share the range budgeted for this role?"

If they insist:
> "Based on my experience and market research for this role, I'm looking at [current CTC + 40-60%]. But I'm open to discussing based on the complete package — role, growth, team, and learning opportunities matter to me."

### After Receiving an Offer

- **Never accept immediately.** "Thank you, I'm very excited about this opportunity. Can I have 2-3 days to review the complete offer?"
- **Negotiate one thing**: If base is fixed, ask about joining bonus, stock, or flexible working.
- **Show enthusiasm**: "I'm genuinely excited about this role. The only thing I'd like to discuss is..."

### Benchmarks (India, 2+ years DE):

| Company Type | Expected Range |
|---|---|
| Service (TCS, Infosys, Wipro) | 4-8 LPA |
| Product (mid-tier) | 10-18 LPA |
| Product (top-tier / unicorn) | 15-30 LPA |
| FAANG / MNC | 25-45 LPA |

---

## THE INTERVIEWER'S HIDDEN SCORECARD

What they're ACTUALLY evaluating:

| What They Ask | What They're Really Checking |
|---|---|
| "Tell me about yourself" | Can you communicate concisely? |
| "Explain your project" | Do you UNDERSTAND what you built, or just copy-pasted? |
| "Why X over Y?" | Do you evaluate trade-offs like a senior engineer? |
| "What if this breaks?" | Do you think about production reliability? |
| "Walk me through the code" | Can you read and explain code fluently? |
| "What would you improve?" | Do you have growth mindset and self-awareness? |
| "Any questions for us?" | Are you genuinely interested in THIS role? |
| Coding problem | Can you think systematically under pressure? |
| Behavioral question | Will you be a good teammate? Handle conflict? Learn? |

---

## PRE-INTERVIEW CHECKLIST

```
[ ] Resume printed / open on screen
[ ] Both projects accessible (GitHub links, running locally if possible)
[ ] Water bottle nearby
[ ] Quiet room, good lighting, camera working
[ ] Read File 00 study order
[ ] Read File 12 quick reference (refresh definitions)
[ ] Practiced 30-second pitch OUT LOUD (not just in your head)
[ ] Prepared 3 questions to ask them
[ ] Salary range decided (with flexibility)
[ ] Know the company's product / what they do
[ ] Confident mindset: "I built two production AI systems. I'm ready."
```
