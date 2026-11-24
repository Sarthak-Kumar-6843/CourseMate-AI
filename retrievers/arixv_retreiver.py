from langchain_community.retrievers import ArxivRetriever


#create retreiver
retriever = ArxivRetriever(
    load_max_docs=2,#no. of papers to retrieve
    load_all_available_meta=True
)
#query arxiv
docs = retriever.invoke("Large language models")

#print reults
for i,doc in enumerate(docs):
    print(f"\nResult {i+1}")
    print("Title:", doc.metadata.get("Title"))
    print("Authors:", doc.metadata.get("Author"))
    print("Summary:", doc.page_content[:500]) # print first 500 char

