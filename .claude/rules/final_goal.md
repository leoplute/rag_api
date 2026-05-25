## Final Goal

# Main Goal
Build an API with FastAPI. Starting with a few main endpoints. The first would
be simply to chat with the locally running llama3.2:3b model via ollama. Other
endpoints would be to add your own files to a request to train, and we chunk and
embed their files into the system to give them more specific answers on their
submitted data. Then also, we would have an endpoint to un-embed certain data, that 
way if it's later deemed bad data, it can be removed from the AI context.

This API is meant to be for general usage. So when I'm creating other projects and
want to throw in an AI apsect, I can run this API and give it some program-specific
data to embed to get more program-specific AI answers. Because of this wanting to be
used by multiple programs, please make sure to take advantage of ChromaDD's collections
to have persistent, program-specific trained data ready for the system.

I do NOT want this to be a user interface centered tool at all. I want to focus on
the backend as much as possible.

# Other Goals
A main goal of this is to get much better with using Claude Code to create programs. I have
never used Claude Code and want to practice with it and understand its capabilities. Because of
this, please frequently recommend ways to improve the experience or get better answers.

Another goal is to build something genuinely useful and impressive. A simple RAG API would be cool
and have use, but I want to have some sort of 'wow' backend features that differentiate my RAG API
from the others. Some ideas would be to make algorithms that append to user provided context docs
with very AI friendly language before embedding for better retrieval of facts. On top of that we could 
improve user prompts before sending them off to chats to improve answers. Beyond that, I don't have
many ideas, but I am very open to some very cool backend tasks, that might take a while to make useful
and to make truly work, so please suggest ideas frequently.