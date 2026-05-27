## Session Cleanup & Resource Management Rules

# Session Termination Triggers
Actively monitor for explicit closing phrases from the user, including but not limited to:
* "done for the day"
* "session is done"
* "wrap it up"
* "cleanup the workspace"
* "cleanup background tasks"
* "cleanup"

# Mandatory Cleanup Protocol
The moment a termination trigger is detected, you MUST execute a full environmental sweeping pass before outputting your final message.

### Step 1: Identify and Kill Subprocesses
* Check for any background tasks, detached scripts, or mock endpoints spawned during this development session.
* Explicitly terminate any orphaned Python processes, file watchers, or local streaming test instances initialized via the shell. 

### Step 2: Resource Verification
* Ensure no dangling ports or background resource-hogs remain active from tools or test suites run during the session.
* Do not attempt to kill the core Ollama daemon, as that is managed externally by the user.

### Step 3: Exit Report
Conclude the session by providing a bulleted checklist confirming exactly what was cleaned up, ensuring the user has full visibility into their system resource states. Example:
> * Terminated 2 background python test instances.
> * Cleared active temporary watch processes.
> * Workspace clean.