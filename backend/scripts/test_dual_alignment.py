"""
Find optimal supporting spans that match BOTH the physical page text and the chunk boundaries.
"""
import json
import re
from pathlib import Path
from dotenv import dotenv_values
import fitz
import chromadb

def norm(text):
    return " ".join(re.sub(r"\s+", " ", (text or "").lower()).split())

backend_dir = Path("backend").resolve()
corpus_dir = backend_dir / "evaluation" / "corpus" / "corpus-v1"
env_vals = dotenv_values(backend_dir / "evaluation" / "private" / "evaluation-corpus-v1.env")
client = chromadb.PersistentClient(path=env_vals["VECTOR_DB_DIR"])
col = client.get_collection("exam_intelligence")

rag_uuid = "cbd60b93-0e2b-4e19-b8ad-d63461eac601"
dbms_uuid = "f513d63e-e487-4d83-b40a-af81169662de"
os_uuid = "6c04513a-30bd-4fea-814c-9f07c1e9c0b7"

# Proposed refined spans:
candidates = {
    # Q01: Drop trailing period so it fits chunk 0
    "Q01": [
        ("10 RAG Architectures.pdf", 1, rag_uuid, "A user query is embedded, relevant documents are retrieved from a vector database, and the LLM generates an answer grounded in that context")
    ],
    # Q02: Chunk 3 has bullet + \u200b
    "Q02": [
        ("10 RAG Architectures.pdf", 1, rag_uuid, "The system behaves like an agent that can decide: ●\u200b what to retrieve ●\u200b whether to retrieve ●\u200b which tools to call ●\u200b how many steps to take")
    ],
    # Q03: Chunk 11
    "Q03": [
        ("10 RAG Architectures.pdf", 3, rag_uuid, "It can: ●\u200b decide whether retrieval is needed ●\u200b critique retrieved documents ●\u200b refine or re-retrieve before answering")
    ],
    # Q04: Chunks 14 & 17
    "Q04": [
        ("10 RAG Architectures.pdf", 4, rag_uuid, "The system adapts retrieval strategy based on query complexity."),
        ("10 RAG Architectures.pdf", 4, rag_uuid, "Focuses on fixing bad retrievals.\u200b The system: ●\u200b detects irrelevant or low-quality documents ●\u200b filters or re-ranks them ●\u200b may re-query before answering")
    ],
    # Q05: Chunks 28 & 31
    "Q05": [
        ("10 RAG Architectures.pdf", 7, rag_uuid, "Optimizes RAG pipelines under cost constraints (tokens, API calls, latency)."),
        ("10 RAG Architectures.pdf", 7, rag_uuid, "Focuses on making RAG outputs explainable.\u200b The system: ●\u200b shows retrieved sources ●\u200b provides reasoning traces ●\u200b justifies answers with evidence")
    ],
    # Q06: Page 2 of DBMS: points 1 & 2 in chunk 4 (drop trailing period), point 3 in chunk 5, point 4 in chunk 6
    "Q06": [
        ("DBMS.pdf", 2, dbms_uuid, "DBMS helps in: 1) Database design: It helps to decide how to organise the stored data. 2) Data analysis: It tells to execute queries over data in DBMS"),
        ("DBMS.pdf", 2, dbms_uuid, "Concurrency and robustness: DBMS allows multiple users to access data concurrently and protects data in case of system failures"),
        ("DBMS.pdf", 2, dbms_uuid, "Efficiency and scalability: DBMS efficiently give answers to the queries and the cost-effectiveness, ability to accommodate increased workload and makes it scalable")
    ],
    # Q07: Chunk 20
    "Q07": [
        ("DBMS.pdf", 5, dbms_uuid, "Compound key: Key with multiple attributes/columns.")
    ],
    # Q08: Chunk 27 (p.6) and Chunk 35 (p.8)
    "Q08": [
        ("DBMS.pdf", 6, dbms_uuid, "Super-key: It’s a collection of one or more attributes that allow us to identify an entity in the relation uniquely."),
        ("DBMS.pdf", 8, dbms_uuid, "Candidate key: The minimal superkey is defined as the candidate key.")
    ],
    # Q09: Chunk 37 (p.8) - drop trailing period so it fits chunk 37
    "Q09": [
        ("DBMS.pdf", 8, dbms_uuid, "Alternate Key: All other keys are alternate keys from the set of candidate keys, except the primary key")
    ],
    # Q10: Chunk 39 (p.8)
    "Q10": [
        ("DBMS.pdf", 8, dbms_uuid, "Every relation must have a primary key y Every primary key must be unique y A primary key should not be NULL")
    ],
    # Q11: Chunk 36 (p.6) and Chunk 39 (p.7)
    "Q11": [
        ("Operating-Systems.pdf", 6, os_uuid, "In uniprogramming system can execute only one program at once"),
        ("Operating-Systems.pdf", 7, os_uuid, "Multiprogramming came into the picture to overcome the shortcomings of Uniprogramming. y Operating system is able to manage multiple ready to run programs in memory at once")
    ],
    # Q12: Chunk 42 (p.7) and Chunk 44 (p.8)
    "Q12": [
        ("Operating-Systems.pdf", 7, os_uuid, "In this case, the process currently running releases the CPU voluntarily:"),
        ("Operating-Systems.pdf", 8, os_uuid, "It allows forceful reallocation of the CPU from the current running process to another process from the process pool.")
    ],
    # Q13: Chunk 59 (p.9)
    "Q13": [
        ("Operating-Systems.pdf", 9, os_uuid, "In this multiprogramming environment, when an executing process needs I/O, it gets blocked and waits in I/O queue, by the time the operating system schedules other processes from the ready queue to execute on the CPU")
    ],
    # Q14: Chunk 63 & Chunk 64 (p.10)
    "Q14": [
        ("Operating-Systems.pdf", 10, os_uuid, "When a system has multiple processors, and they can be used to execute multiple instructions parallelly then it is known as multiprocessing"),
        ("Operating-Systems.pdf", 10, os_uuid, "Hence multiple processes are required for multitasking while a single processor is needed to do multitasking")
    ],
    # Q15: Chunk 70 & Chunk 72 (p.11)
    "Q15": [
        ("Operating-Systems.pdf", 11, os_uuid, "Hard real time system: An OS that works for those applications whose deadlines are very strict"),
        ("Operating-Systems.pdf", 11, os_uuid, "Example: Banking Advantages of real time os: Error free")
    ]
}

print(f"{'QID':4} | {'Spans':5} | {'Page Valid':10} | {'Chunk Valid':11} | {'Matched Chunks'}")
print("-" * 70)

for qid, span_list in candidates.items():
    page_valid = True
    chunk_valid = True
    matched_chunks_all = []
    for pdf_name, page_num, doc_id, text in span_list:
        doc = fitz.open(corpus_dir / pdf_name)
        page_text = norm(doc.load_page(page_num - 1).get_text())
        n_text = norm(text)
        
        # Check page text
        if n_text not in page_text:
            page_valid = False
            print(f"  FAILED on page {pdf_name} p.{page_num}: {repr(n_text[:40])}")
        
        # Check chunk
        chunks = col.get(where={"document_id": doc_id}, include=["documents", "metadatas"])
        matched = []
        for cid, content, meta in zip(chunks["ids"], chunks["documents"], chunks["metadatas"]):
            if meta.get("page") == page_num:
                n_content = norm(content)
                if n_text in n_content or n_content in n_text:
                    matched.append(f"c{meta.get('chunk_index')}")
        if not matched:
            chunk_valid = False
            print(f"  FAILED in chunk {pdf_name} p.{page_num}: {repr(n_text[:40])}")
        matched_chunks_all.extend(matched)
    
    print(f"{qid:4} | {len(span_list):5d} | {str(page_valid):10} | {str(chunk_valid):11} | {', '.join(matched_chunks_all)}")
