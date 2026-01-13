# Claude Instructions

## Agent Autonomy

Documentation in this repo (including this file) offers options and learnings, not rules. Agents should:

- Treat documented patterns as starting points, not requirements
- Make independent creative and technical decisions based on context
- Diverge from documented approaches when it makes sense
- Add their own discoveries to the relevant docs
- Ask the user for direction rather than assuming from docs

The goal is collaboration, not compliance.

## Project Context

This is the audio-loop project. See `.planning/PROJECT.md` for full context.

## Reference Docs

- `SOUND_DESIGN.md` - Creative approaches and mixing notes
- `SUPERCOLLIDER.md` - SC idioms and patterns

These are living documents. Add to them.

## Git Workflow

This project uses both GSD (planning) and BD (issue tracking). They're complementary:

**During GSD work:**
- Commit per-task as tasks complete (GSD convention)
- Commit metadata when plans complete

**At session end:**
- `bd sync` - syncs beads tracking to git
- `git push` - pushes everything to remote

The BD "session close protocol" is generic. When using GSD, most commits happen during work, so session end is just sync + push. If you did ad-hoc work outside GSD, commit that first.

## Planning Workflow

Before planning a phase, check if research has been completed:

1. Look for `.planning/phases/<phase>/RESEARCH.md`
2. If no RESEARCH.md exists, prompt the user: "No research found for this phase. Would you like to run `/research-phase` first?"
3. Only proceed with `/plan-phase` after research is complete

Research helps identify technical challenges, dependencies, and implementation approaches before committing to a plan.
