---
name: what-if-story-scripts
description: Write narrated "What If" animated story scripts for YouTube (the Ifverse style - a hypothetical power or change, a hidden cost, and a human character who pays for it). Interviews the user first (idea, style, length, narration), finds niche trending under-covered ideas, then writes hooks and beat-by-beat scripts. Use this skill whenever the user wants a YouTube script, video idea, hook, or outline for a "what if" channel, faceless animated storytelling, narrated hypothetical or superpower stories, or says things like "give me a video idea", "write a script", "what should my next video be", "make a hook", or "Part 2 of my series" - even if they never name the style.
---

# What-If Story Scripts

Writes scripts for narrated, animated "What If" story videos. The formula: **an appealing power or change + a hidden cost + a specific person who pays for it.** The video is a short story that uses the hypothetical as its engine, not an explainer or a list of facts.

## STEP 0 - INTERVIEW FIRST (mandatory)

**Do not write any idea, hook, outline or script until the interview below is finished.** This applies even if the user's first message already says "write a script". Ask the questions one at a time, in this exact order, and wait for each answer before asking the next. If an answer was already clearly given in the user's message, confirm it in a line instead of re-asking.

If the `ask_user_input_v0` tool is available, use it for questions 2-4 so the user can tap an option. Otherwise show the options as a numbered list and tell the user they can reply with a number or their own words. Always allow a custom answer.

### Question 1 - The idea
Ask:
> **What's your video idea?**
> Type it in, or reply **"give me ideas"** and I'll find niche ones that are trending and under-covered.

- If they give an idea -> go to Question 2.
- If they say "give me ideas" or have none -> ask **Question 1b** below, run the Idea Engine, let them pick one, then go to Question 2.

### Question 1b - Topic area (only if they want ideas)
Ask:
> **What area should the ideas come from?**
> 1. Tech and AI (machines, algorithms, devices)
> 2. Science and biology (the body, brain, space, nature)
> 3. Psychology and emotions (memory, sleep, relationships)
> 4. Society and daily life (money, work, social media, cities)
> 5. Surprise me (mix of everything)

### Question 2 - Style
Ask:
> **What style should the video be?**
> 1. **Tech "What If"** - a technology or AI changes life; grounded, near-future, cool but unsettling
> 2. **Superpower "What If"** - a person gains an ability and pays a hidden cost (the Ifverse style)
> 3. **Survival / extreme scenario** - a ticking clock, rules, and hard choices
> 4. **Emotional drama** - a quiet, character-driven story with a big human moment
> 5. **Dark / thriller twist** - tense, unsettling, ends on a shock
> 6. **Something else** - describe it

The chosen style changes tone, pacing and ending. Read `styles.md` and apply it.

### Question 3 - Video length
Ask:
> **How long should the video be?**
> 1. Short (3-5 min)
> 2. Standard (8 min)
> 3. Long (10-12 min)
> 4. Custom - tell me the minutes

### Question 4 - Narration and format
Ask:
> **How should it be told?**
> 1. Second person ("You...") - immersive, strongest hooks (recommended)
> 2. First person ("I...") - personal and confessional
> 3. Third person ("He / She...") - classic storytelling
>
> And is this a **single video** or **Part 1 of a series**?

(If the tool supports several questions at once, narration and single/series can be asked together.)

### After the interview
Summarize the choices in one short block (Idea, Style, Length, Narration, Series) and ask "Good to go?" only if something was ambiguous. Then continue to the workflow below.

Narration runs about 150 words per minute (5 min ~ 750 words, 8 ~ 1,200, 10 ~ 1,500, 12 ~ 1,800).

## Idea Engine (when the user wants ideas)

Goal: ideas that are **hot now** and **not covered much**, and fit the formula. Read `idea-engine.md` for the scoring rubric and search tactics, then:

1. Use web search to find current signals in the chosen area. Use today's actual date in queries.
2. Search "what if [idea]" style queries to gauge saturation.
3. Generate 5 candidates, each with: title, one-line promise, hidden cost, who pays, why it's timely, saturation note.
4. Be honest about evidence. Say "I found few existing videos", never invent view counts or claim "nobody has covered this."
5. Recommend one and say why. Let the user choose or remix. Then continue the interview at Question 2.

## Idea check (when the user brings an idea)

Make sure the idea has all three parts. If one is missing, fix it with the user in 2-3 lines:
- **Appealing power or change**: would people want this?
- **Hidden cost**: can it be stated in one sentence?
- **A person who pays**: a character with someone to lose.

If the idea is generic, propose a sharper, more niche angle before continuing.

## Script workflow

1. **One-line promise.** "A [person] gets [power], and finds out the real cost is [cost]."
2. **10 hooks.** Label each hook's type, score against `hook-checklist.md`, recommend two. User picks or mixes. Never open with a greeting or channel intro.
3. **Outline.** Scale the beat map in `structure.md` to the chosen length. Show as a short table.
4. **Write one beat at a time**, following `style-guide.md` and the chosen style. After each beat give a 1-line retention note and ask: continue, adjust, or rewrite?
5. **Emotional centerpiece.** One extended scene with a specific relationship and real dialogue. Never skip it.
6. **Ending.** Cut before the decision, land on one quiet line, then a Part 2 hook (if a series).
7. **Final pass.** Check against the hook checklist and style guide. Remove passive voice, vague words, and lines that explain what visuals already show. Verify any real-world fact or study, or leave it out.

## Output format

- Narration lines only, short paragraphs, ready for voiceover. Add `[VISUAL: ...]` notes sparingly.
- Timestamps at beat starts.
- End with 3 working titles, one thumbnail concept, and the Part 2 teaser (if a series).
- If the script is long, offer to put it in a document.

## Non-negotiables

- Never skip the interview in Step 0.
- Concrete over abstract: specific numbers, objects, textures, dates.
- Real-world grounding for the cost. Flag anything needing verification.
- No dry academic summaries. Every fact is tied to a human stake.
