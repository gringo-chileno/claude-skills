# Claude Code Skills

Shareable skills for [Claude Code](https://claude.ai/claude-code).

## Installation

Copy any skill folder into your `~/.claude/skills/` directory:

```bash
# Clone this repo
git clone https://github.com/gringo-chileno/claude-skills.git

# Copy a skill to your Claude Code skills directory
cp -r claude-skills/vacation-planner ~/.claude/skills/
```

Then restart Claude Code. The skill will appear as a `/vacation-planner` slash command.

## Available Skills

### `/vacation-planner`

Plan a family or group vacation with destination research, real flight searches, sample itineraries, and a photo-rich PowerPoint presentation for voting.

**What it does:**
1. Gathers trip requirements (travelers, dates, budget, interests)
2. Researches and compares destinations (weather, activities, logistics, pros/cons)
3. Searches real flights via Chrome DevTools + Google Flights
4. Builds a polished PowerPoint with photos for the group to vote on destinations

**Requirements:**
- Python packages: `python-pptx`, `Pillow`, `requests`
- Chrome DevTools MCP server (for live flight searches)
- Optional: Gemini API key for AI-generated photos (works without it using Wikimedia Commons)

**Usage:**
```
/vacation-planner family trip to South America in September
```
