# RAG API for General Program Usage

## Project Goal
Building a local RAG system using LLama3.2:3b model, likely scaling
up to the 8b parma model soon. Along with that, the all-minilm:22m model
is being used for embedding, but will be open to changing as the project
scales if needed. With those tools, build an intutive and useful API 
exposing the RAG system to users who can give theur own files as context
and chat with the RAG system.
Please refer to deeper goals for more at `.claude/rules/final_goal.md`

## Architecture
Language: Python 3.12
Environment Manager: uv
Vector DB: ChromaDB persistent

## Code Style
Refer to `.claude/rules/syntax_rules.md` for exact code styling, project
structure preferences, and commenting choices.

## Core Commands
'uv run main.py' - To turn on the RAG API
'uv add ...' where ... is the name of any dependency we are adding 
to the python project
    ** ALWAYS check with me before adding libraries to the project

Please refer to `.claude/rules/bad_commands.md` for guidelines regarding bash commands to never run.

## Testing
Refer to `.claude/rules/testing.md` for how to test your additions

## Domain-Specific Rule Maps

Ollama & Local RAG: For any tasks, architecture designs, script creations, or debugging loops involving Ollama, local LLMs (1B, 3B, 8B), embedding models, or ChromaDB, you **MUST** read and adhere to the strict execution boundaries defined in `.claude/rules/ollama_rules.md`.

Prioritize Local Guardrails: Never default to high-level cloud API patterns if a local implementation strategy is specified in the Ollama rules file.

## Cleanup
At the end of conversations or when the context window gets close to condensing,
ALWAYS clean up any backend tasks or processes started to help claude code run
agentically.
Further cleanup rules exist at `.claude/rules/cleanup_rules.md`