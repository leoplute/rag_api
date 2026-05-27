## Testing

# Testing Flow
1. Clear the old embedded data (the txt files from @test_docs/)
from the persistent ChromaDB
  - Do this to ensure that we the new changes in the pipeline
    actually run and re-emebed before getting a response

2. Re-embed the 3 recent Utah news txt files from @test_docs/
into the persistent ChromaDB (can all be in one 'testing' 
collection)

3. Chat with the RAG system

4. Ensure the answers you are receiving from the RAG system include
the information we are embedding into ChromaDB by checking the JSON
file with expected answers
  - Locate the JSON file with the specifics expected from certain
    questions is at @test_docs/expected_answers.json

5. If any of the questions you are asking are not giving back the
specifics about these topics we are embedding into the RAG system,
continue to iterate your code until all the responses are giving
expected answers.



# JSON Tests
The JSON file at @test_docs/expected_answers.json contains a bunch
of question/answer pairs for each of the 3 txt files we are using
to test the embedding. These questions/answer pairs all contain
specific data that is mentioned in the txt files we are embedding,
so that we can make sure the RAG system is using the embedded and
stored, user-inputted data for its answers.



# Iteration
Use these JSON tests as a way of testing your work. After making 
substantial changes to the code in any way (adding or removing),
spin up the RAG system and ask it some the questions from the JSON
file and ensure the answer from the RAG system contains the specific
data in the corresponding answer in the JSON file