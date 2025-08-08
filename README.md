
## Module 1: Offline indexing pipeline
#### Data preperation stage. Goal to convert the raw documents into highly efficient. searchable vector index.
- Step 1: Load and chunk Documents: You read the documents (PDFs, text files, etc.) and break their content into smaller, overlapping chunks. A chunk might be a paragraph or a few sentences. This is better than embedding a whole document because it provides more specific context for the LLM.
- Step 2: Embed the chunks: You convert each text chunk into a numerical vector (an "embedding") using a pre-trained sentence-transformer model. These vectors capture the semantic meaning of the text.
- Step 3: Store in a vector database : take all the embeddings and store them in a special database designed for extremely fast similarity searches.
## Module 2: Online inference pipeline
#### Active part that answers user queries
- Step 4: Retrieve relavent chunks
	- When a user enters a query, you first embed their query using the _exact same model_ from Step 2. Then, you use your FAISS index to find the text chunks with embeddings most similar to the query's embedding.
- Step 5: Generate an answer
	- You take the retrieved chunks from Step 4 and format them into a single piece of context. You then create a precise prompt that instructs your offline LLM to answer the user's query based _only_ on that context.

This is the basic logical breakdown of the problem, once this is done we can start to implement re-ranking ( or re-ranker ).
