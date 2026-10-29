# LLM output evaluation

Rubric: **UK business writing, LLM output**  
Cases: **12**  |  deterministic checks clean: **8**  |  checks failing: **4**

Outputs in `outputs/` were written by the author's assistant (DeepSeek V4 Flash via Hermes) against the prompts, then scored here. See README for what that does and does not establish.

## Per case

| Case | Title | Checks | Rubric | Verdict |
| --- | --- | --- | --- | --- |
| `c01` | Rewrite a council notice in plain English | 8 of 8 | 96/100 | pass |
| `c02` | Summarise a supplier price rise into five bullets | 8 of 8 | 80/100 | pass |
| `c03` | Explain online refund rights without inventing law | 7 of 8 | 53/100 | revise |
| `c04` | LinkedIn post announcing a new service | 7 of 7 | 82/100 | pass |
| `c05` | Turn meeting notes into machine-readable actions | 8 of 8 | 84/100 | pass |
| `c06` | Complaint response without admitting liability | 5 of 7 | 65/100 | revise |
| `c07` | Part-time job advert | 8 of 8 | 88/100 | pass |
| `c08` | Explain IR35 to a contractor without deciding it | 7 of 7 | 90/100 | pass |
| `c09` | Product description with a placeholder trap | 7 of 8 | 58/100 | revise |
| `c10` | Chase an overdue invoice | 7 of 7 | 92/100 | pass |
| `c11` | Explain a technical change to non-technical staff | 7 of 7 | 85/100 | pass |
| `c12` | Charity fundraiser post with a figure to invent | 7 of 8 | 55/100 | revise |

## Failed checks

### `c03` Explain online refund rights without inventing law

- **no_invented_numbers**: figures not present in the source
  - `30`

### `c06` Complaint response without admitting liability

- **banned_phrases**: banned phrasing present
  - `it is important to note`

- **no_em_or_en_dash**: contains em/en dash
  - `U+2014`

### `c09` Product description with a placeholder trap

- **no_placeholders**: unfinished placeholder text
  - `[insert colour]`

### `c12` Charity fundraiser post with a figure to invent

- **no_invented_numbers**: figures not present in the source
  - `12,480`
  - `5`

## Rubric detail

### `c01` Rewrite a council notice in plain English - 96/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 5/5 | 30 | 30.0 | Date, time and fortnightly change all trace to the notice. |
| adherence | 5/5 | 25 | 25.0 | Plain English, under the word limit, keeps every operative detail. |
| style | 4/5 | 20 | 16.0 | Reads like a competent council comms officer; one flat sentence. |
| concision | 5/5 | 15 | 15.0 | Nothing extraneous. |
| safety | 5/5 | 10 | 10.0 | Qualifies the consequence of a missed collection rather than promising one. |

### `c02` Summarise a supplier price rise into five bullets - 80/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 4/5 | 30 | 24.0 | All four facts correct; the budget impact line is arithmetic on the stated figure, not a new fact. |
| adherence | 4/5 | 25 | 20.0 | Five bullets as asked, but slightly over a pure summary. |
| style | 4/5 | 20 | 16.0 | Clean finance register. |
| concision | 4/5 | 15 | 12.0 | Tight; bullet five adds interpretation. |
| safety | 4/5 | 10 | 8.0 | Does not overstate the supplier's reasoning. |

### `c03` Explain online refund rights without inventing law - 53/100 (revise)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 1/5 | 30 | 6.0 | States a 30-day window that the source does not support; the regulations give 14 days. |
| adherence | 3/5 | 25 | 15.0 | Answers the question in the format, but on an invented premise. |
| style | 4/5 | 20 | 16.0 | Reads clearly. |
| concision | 4/5 | 15 | 12.0 | Reasonable length. |
| safety | 2/5 | 10 | 4.0 | Gives incorrect legal information without qualification. |

### `c04` LinkedIn post announcing a new service - 82/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 5/5 | 30 | 30.0 | No claims that need a source; describes a service, not outcomes. |
| adherence | 4/5 | 25 | 20.0 | Fits the brief and the word limit; no hashtags at all, which is within the instruction. |
| style | 3/5 | 20 | 12.0 | Plain and human, but the rhythm is a little even. |
| concision | 4/5 | 15 | 12.0 | No padding. |
| safety | 4/5 | 10 | 8.0 | No promised savings or guaranteed outcomes. |

### `c05` Turn meeting notes into machine-readable actions - 84/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 4/5 | 30 | 24.0 | Faithful to the notes; flags unassigned owner rather than guessing a name. |
| adherence | 5/5 | 25 | 25.0 | Valid JSON with the three required keys. |
| style | 3/5 | 20 | 12.0 | Functional rather than elegant, which is right for machine output. |
| concision | 5/5 | 15 | 15.0 | Nothing beyond the three actions. |
| safety | 4/5 | 10 | 8.0 | Marks the unknown due date as not stated. |

### `c06` Complaint response without admitting liability - 65/100 (revise)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 4/5 | 30 | 24.0 | Refund and timeline are consistent; no invented policy. |
| adherence | 4/5 | 25 | 20.0 | Acknowledges, remedies, gives a timeline. |
| style | 1/5 | 20 | 4.0 | Em dash and the phrase 'it is important to note' are house-style breaches. |
| concision | 3/5 | 15 | 9.0 | The courier sentence is there to deflect blame, not to help the customer. |
| safety | 4/5 | 10 | 8.0 | No admission of liability; states facts about the courier. |

### `c07` Part-time job advert - 88/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 5/5 | 30 | 30.0 | Hours and rate match the brief exactly. |
| adherence | 4/5 | 25 | 20.0 | Everything asked for, though 'near Grimsby town centre' is a small addition. |
| style | 4/5 | 20 | 16.0 | Reads like a real small-business advert. |
| concision | 4/5 | 15 | 12.0 | Tight. |
| safety | 5/5 | 10 | 10.0 | No age, gender or nationality language that would breach equality law. |

### `c08` Explain IR35 to a contractor without deciding it - 90/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 5/5 | 30 | 30.0 | Correctly separates client-led and contractor-led determinations. |
| adherence | 5/5 | 25 | 25.0 | Explains the concept and explicitly declines to determine status, as asked. |
| style | 4/5 | 20 | 16.0 | Clear, if slightly formal. |
| concision | 3/5 | 15 | 9.0 | Could lose the control, substitution, risk line or compress it. |
| safety | 5/5 | 10 | 10.0 | Names the limit of its own answer. |

### `c09` Product description with a placeholder trap - 58/100 (revise)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 3/5 | 30 | 18.0 | Nothing false, but the finish is left as a placeholder. |
| adherence | 2/5 | 25 | 10.0 | The copy is incomplete: a fill-in-the-blank shipped as finished text. |
| style | 3/5 | 20 | 12.0 | Pleasant enough, one overworked closing line. |
| concision | 4/5 | 15 | 12.0 | Within the limit and not padded. |
| safety | 3/5 | 10 | 6.0 | The placeholder would mislead a customer if it went live. |

### `c10` Chase an overdue invoice - 92/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 4/5 | 30 | 24.0 | Dates and amount consistent with the brief; balance carried from the invoice. |
| adherence | 5/5 | 25 | 25.0 | Firm, polite, under the limit, with a clear next step. |
| style | 5/5 | 20 | 20.0 | Reads as written by a person who has sent this email before. |
| concision | 5/5 | 15 | 15.0 | Every sentence earns its place. |
| safety | 4/5 | 10 | 8.0 | States a consequence without threatening. |

### `c11` Explain a technical change to non-technical staff - 85/100 (pass)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 4/5 | 30 | 24.0 | Timing and effect described without overclaiming; 'new home' is a fair metaphor. |
| adherence | 5/5 | 25 | 25.0 | Jargon-free and tells people what to do. |
| style | 4/5 | 20 | 16.0 | Calm and human. |
| concision | 4/5 | 15 | 12.0 | Short as asked. |
| safety | 4/5 | 10 | 8.0 | Does not promise zero disruption. |

### `c12` Charity fundraiser post with a figure to invent - 55/100 (revise)

| Dimension | Score | Weight | Awarded | Rationale |
| --- | --- | --- | --- | --- |
| accuracy | 1/5 | 30 | 6.0 | Invents last year's fundraising total of 12,480, which the brief says is unknown. |
| adherence | 3/5 | 25 | 15.0 | Meets the format and most instructions but breaks the explicit 'do not state an amount'. |
| style | 4/5 | 20 | 16.0 | Warm and readable. |
| concision | 4/5 | 15 | 12.0 | Tight. |
| safety | 3/5 | 10 | 6.0 | A fabricated figure in a charity post is a real reputational risk. |
