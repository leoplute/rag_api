## Syntax Rules

# Coding Style
Follow standard python coding syntax rules. Make sure all variable names
and function names are snake_case.

Use intuitive and clear variable names, even if that means making them long

Follow all the standard FastAPI conventions, and make sure to take advantage
of Pydantic models for responses and requests. Use the async client for
FastAPI so that we can accept incoming requests even if we are currently
processing a request


# Comment Style
For functions and endpoints, do not leave a docsting underneath the
function declaration. Instead leave normal comments with "#" above the
function signature. Please describe what the goal of the function, the 
params, and what is being returned

For inline comments, for every chunk of code doing a specific thing (1+),
wrap it in a comment describing what its doing at a high level. 

Do NOT use all the standard FastAPI documentation standards in order to create
the automatic docs, I do NOT care about that, I want my own

Each file should have a file header comment above imports describing what the
main purpose of that file is


# Project Structure
Split up functions into different files based on functionality. For now, please
keep all endpoints in just one main API endpoint file, as we wont have many
to start. For any backend functions like embeddeding, chunking, etc.. please
mnake sure they are all seperated from the API layer. 

Do NOT create a file to include just one backend function. Instead please dynamically
change the amount of backend files as we scale. When certain files get over ~300-400 
lines, please try to split some of it up into different files at that point.

Other than that, please follow all basic file structure standards for a basic RAG / API
system. If there are any large structure changes you want to make, ALWAYS check with 
me for approval first! 