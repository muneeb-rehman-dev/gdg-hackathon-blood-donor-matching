# 🩸 Real-Time Blood Donor Matching over WhatsApp

## The Problem

When a patient urgently needs blood in Karachi, finding eligible donors is often chaotic and time-consuming. Families post requests across WhatsApp groups, call hospital administrators, message Facebook pages, and circulate donor information that may be outdated, inaccurate, or irrelevant.

While Al-Khidmat maintains a large network of verified blood donors across multiple blood groups and neighborhoods, access to this network currently depends on human coordinators. This process does not scale during emergencies, late-night requests, or periods of high demand.

The challenge is not simply finding donor names—it is finding **eligible, reachable donors who are willing to commit**, without overwhelming the entire donor database, exhausting frequent responders, or forcing distressed families to manage follow-ups themselves.

---

## Who Initiates a Request?

Anyone can initiate a blood request:

* Patient family members
* Hospital staff
* Members of the public

Requests arrive through WhatsApp and are often written under stressful circumstances using:

* Urdu
* Roman Urdu
* English
* Mixed-language messages

The system must be capable of understanding incomplete, informal, and unstructured requests.

---

## Where AI Adds Value

### 1. Natural Language Intake

Users send messages such as:

> "Need 5 O+ donors near Gulshan urgent, patient at Indus Hospital"

or

> "AB negative chahiye jaldi, Liaquat National mein"

An LLM extracts structured information including:

* Blood group
* Required donor count
* Hospital
* Location
* Urgency level

If critical information is missing, the system asks intelligent follow-up questions.

---

### 2. Intelligent Donor Ranking

Instead of broadcasting requests to all matching donors, the system prioritizes candidates using a composite ranking score based on:

* Distance from the hospital
* Blood donation eligibility (time since last donation)
* Historical response rate
* Time of day
* Recent request frequency (to prevent donor fatigue)

This ensures the most likely responders are contacted first.

---

### 3. Wave-Based Outreach

The system contacts donors in controlled waves.

**Example:**

* Wave 1: Top 8–10 ranked donors receive the request.
* If the target is not met within a defined timeframe, Wave 2 is triggered automatically.
* Additional waves continue until sufficient donors commit.

The requester receives live progress updates:

> 3 of 5 donors confirmed

This approach minimizes unnecessary outreach while maximizing successful matches.

---

### 4. Conversational Donor Understanding

Donors respond naturally, and the AI interprets intent.

Examples:

| Donor Message                 | System Action                                   |
| ----------------------------- | ----------------------------------------------- |
| "I donated blood last month." | Updates eligibility status                      |
| "Kal subah aa sakta hoon."    | Records availability and schedules confirmation |
| "Out of Karachi this week."   | Marks temporarily unavailable                   |

The system understands context rather than relying on rigid button-based workflows.

---

## Constraints & Requirements

### Language Support

* Urdu
* Roman Urdu
* English
* Mixed-language conversations

### Channels

* WhatsApp as the primary interface
* Coordinator dashboard as a secondary interface

### Hackathon Scope

For demonstration purposes:

* WhatsApp can be simulated through a chat-style web interface.
* The demo should showcase the complete request-to-confirmation workflow.

### Data

* Synthetic donor dataset (200+ records)
* Multiple blood groups
* Multiple neighborhoods
* Last donation dates included

### Privacy

* No real personal data
* No real SMS or WhatsApp integration required
* No actual donor outreach performed

---

## Expected Outcome

A deployed web application that demonstrates the complete donor-matching workflow:

1. A requester submits a blood request through a chat interface.
2. The system extracts structured information using AI.
3. Donors are ranked and contacted in simulated outreach waves.
4. Live commitment counts are displayed in a coordinator dashboard.
5. A final summary of confirmed donors is generated for action.

### Bonus

Demonstrate donor-side conversational understanding and automatic record updates based on natural-language responses.

---

## Why This Matters

Al-Khidmat's strength is its trusted volunteer network of more than **25,000 verified donors**.

The challenge is not collecting donor data—it is creating an effective interface between a stressed requester and that network during time-critical emergencies.

By automating intake, ranking, outreach, and follow-up, this project addresses a real operational bottleneck in Karachi's emergency medical response system and helps connect patients with lifesaving donors faster.
