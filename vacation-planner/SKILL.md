---
name: vacation-planner
description: Plan a family or group vacation with destination research, real flight searches, sample itineraries, and a photo-rich PowerPoint presentation for voting. Use when the user wants to plan a trip, compare vacation destinations, or create a travel presentation.
argument-hint: [destination or trip description]
---

# Vacation Planner Skill

Research, compare, and present vacation destinations — ending with a polished PowerPoint presentation the family/group can use to vote.

## Workflow Overview

The skill follows 4 phases. Don't rush — each phase needs user input before moving on.

### Phase 1: Gather Requirements

Ask the user (don't assume):
- **Who's going?** (adults, kids + ages, special needs)
- **Flying from where?**
- **When?** (exact dates or flexible window)
- **Budget level?** (budget / mid-range / flexible / luxury)
- **Interests?** (beach, adventure, culture, wildlife, relaxation, food)
- **Destinations already in mind?** (starting points, not final list)
- **Dealbreakers?** (altitude issues, heat sensitivity, long travel days with young kids, etc.)

### Phase 2: Research & Compare Destinations

For each destination, research and present:

1. **Getting there** — Flight routes, connections, travel time from origin city
2. **Weather** — Temperature (use Fahrenheit), rain/dry season, comfort level for travel dates
3. **Activities** — What you'd actually DO there, organized by type. Present facts, don't editorialize ("kids will LOVE this" — let them decide)
4. **Sample itinerary** — Day-by-day outline showing a realistic pace
5. **Logistics** — Internal transport (flights, boats, drives), complexity level
6. **Budget estimate** — Flights + accommodation + activities ballpark
7. **Pros / Cons** — Honest assessment, including dealbreakers

**Research tools:**
- Use `WebSearch` for destination info, weather data, activity research
- Use Chrome DevTools MCP tools for live flight searches (see Flight Search section below)
- Present findings in clean comparison tables

**Iterate with user:** After initial research, ask which destinations to keep, drop, or add. Narrow to 4-6 options for the presentation.

### Phase 3: Flight Search

Use Chrome DevTools MCP tools to search Google Flights for real pricing and schedules.

#### How to search flights:

1. **Load tools:** Use ToolSearch to load `mcp__chrome-devtools__navigate_page`, `mcp__chrome-devtools__wait_for`, and `mcp__chrome-devtools__take_snapshot`

2. **Navigate to Google Flights** with a pre-filled search URL:
   ```
   https://www.google.com/travel/flights?q=Flights+to+{DEST_CODE}+from+{ORIGIN_CODE}+on+{YYYY-MM-DD}+through+{YYYY-MM-DD}&curr=USD&hl=en
   ```
   Example: `https://www.google.com/travel/flights?q=Flights+to+GIG+from+SCL+on+2026-09-12+through+2026-09-20&curr=USD&hl=en`

3. **Wait for results:** Use `wait_for` with text `["stops", "nonstop", "Nonstop", "results returned", "No results", "Oops"]` and timeout 15000ms

4. **If "Loading results" still showing**, take a snapshot and wait again with longer timeout

5. **Read the accessibility tree snapshot** — flight details are in `link` elements with full text descriptions including departure/arrival times, duration, stops, and prices

6. **If "No results returned"** — the route may be too far in the future for smaller airports. Try:
   - Search domestic legs separately (e.g., GRU→CGB instead of SCL→CGB)
   - Use a closer date to get representative schedules, then note "schedules may change"
   - Common hubs: GRU (São Paulo), GIG (Rio), EZE (Buenos Aires), BOG (Bogotá), LIM (Lima)

7. **Present results** in a clean table: Depart, Arrive, Duration, Stops, Price (RT)

#### Tips:
- Search multiple routes in sequence (the browser can only show one page at a time)
- For round trips, Google Flights shows outbound first — click a flight to see return options, or search the reverse route separately
- Note whether prices are per-person round-trip or one-way
- Flag when nonstop options exist vs. connection-only routes — this matters a lot for families

### Phase 4: Build the Presentation

Generate a PowerPoint using Python `python-pptx`. The presentation should let the group compare destinations and vote.

#### Prerequisites
```bash
pip install python-pptx Pillow requests
```

#### Photo Sourcing Strategy

Ask the user which approach they'd like:

**Option A: Wikimedia Commons only (free, no API key needed)**
- Real photos from Wikimedia Commons. Works well for famous landmarks and popular destinations.
- Some niche destinations may have limited or low-quality options.
- Use the Wikimedia API to search and find URLs:
  ```python
  params = {"action": "query", "generator": "search", "gsrsearch": "Chapada Diamantina waterfall",
            "gsrnamespace": "6", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": "1280", "format": "json"}
  headers = {"User-Agent": "VacationPlanBot/1.0 (vacation planning)"}
  ```
  **Download with curl** (Python requests gets 403 from Wikimedia):
  ```python
  subprocess.run(["curl", "-sL", "-o", path, "-H",
                   "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", url])
  ```
  Add `time.sleep(2)` between downloads to avoid rate limiting.

**Option B: Wikimedia + Gemini API (best quality, requires API key)**
- Use Wikimedia for photos that are readily available, Gemini to fill gaps.
- Requires a Google Gemini API key. Check `.env` for `GEMINI_API_KEY`, or ask the user to provide one.
- Gemini generates photorealistic travel images on demand — useful for specific scenes (aerial views, underwater caves, etc.) where free stock is limited.
  ```python
  # Model: gemini-2.0-flash-exp-image-generation
  url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}"
  payload = {
      "contents": [{"parts": [{"text": f"Generate a photorealistic travel photograph: {prompt}. Professional travel magazine quality, vibrant colors, landscape 16:9."}]}],
      "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }
  # Response contains base64 image in candidates[0].content.parts[].inlineData.data
  ```

**Always include placeholder fallback** — If any photo fails to download or generate, show a colored rectangle with the key name so the user knows what's missing and can retry.

#### Slide Structure

For each destination (5 slides):
1. **Hero slide** — Title + tagline + key facts (flight, weather, duration, budget) + hero photo
2. **Photos slide** — 4 photos in a row with captions
3. **Activities slide** — Two-column bulleted list of what you'd do there
4. **Plan slide** — Three-column layout: itinerary | pros | cons + budget footer
5. **Flight slide** — Real flight data table (outbound options + return info + notes)

Plus:
- **Title slide** — Trip name + dates + thumbnail of each destination
- **Comparison slide** — Numeric scores (1-5) table with categories + averages. Color-code: green=5, white=4, gray=3, coral=2
- **Voting slide** — Thumbnails + names, prompt to vote

#### Design Guidelines

- **Widescreen:** 13.333" x 7.5" (16:9)
- **Dark theme:** Navy background (#1a1a2e), gold accents (#ffd700), white text
- **Color per destination:** Assign each destination a distinct accent color (orange, green, cyan, gold, coral, etc.)
- **Font sizes:** Titles 28-40pt, body 14-17pt, captions 11-13pt. Bigger is better — this is for viewing on a TV/projector
- **No "kids will love this"** language — present facts, let the audience decide
- **Temperatures in Fahrenheit** (or ask user preference)
- **Resize photos** to max 1920px before embedding to keep file size reasonable

#### Python Script Template

See `PPTX_TEMPLATE.md` in this skill directory for a complete, working Python script template with all slide builder functions.

## Key Principles

1. **Iterate, don't dump** — Present research in stages, get feedback, refine
2. **Be honest about cons** — A vacation ruined by altitude sickness or 12-hour travel days is worse than no vacation
3. **Logistics matter** — The "best" destination on paper might be terrible if getting there takes 14 hours with 2 connections and a 4-hour drive
4. **Show, don't tell** — The PowerPoint exists so the family can SEE the destinations, not just read about them
5. **Respect the audience** — Don't be patronizing about what's "fun" or "exciting." Present the information and let people choose
6. **Budget transparency** — Always estimate total trip cost (flights x number of people + accommodation + activities), not just per-person flight price
