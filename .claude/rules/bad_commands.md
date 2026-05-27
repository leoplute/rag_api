## Security & Command Execution Boundaries

### 1. Hard Constraints (Never Execute Automatically)
- **Destructive Deletions:** Never run `rm -rf` on any directory outside of specific local project build/cache artifacts (e.g., `__pycache__`). Never target `~`, `/`, or use variables in a deletion command.
- **Global State Alteration:** Do not modify system-level configurations, shell profiles (`.zshrc`, `.bashrc`), or global environment files.
- **Untrusted Execution:** Never pipe internet content directly into a shell (e.g., `curl ... | sh`).
- **Directory Isolation:** Do not move (`mv`), copy (`cp`), or write (`>`) files outside the project workspace, with the sole exception of writing temporary logs to `/tmp/`.

### 2. High-Risk Escalation Protocol
If you determine that a command bordering on or falling into the high-risk categories above is **absolutely necessary** to proceed with development:
1. You **MUST** explicitly flag it before asking for permission.
2. Prefix your permission request with the exact string: `⚠️ [HIGH-RISK COMMAND DETECTED]`.
3. Provide a 1-sentence plain-English explanation detailing exactly what the command does, what it alters, and why a safer alternative is not possible.