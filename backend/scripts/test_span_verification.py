"""
Verify exact span normalization matching against PyMuPDF page text.
"""
import fitz
import re
from pathlib import Path

corpus_dir = Path("backend/evaluation/corpus/corpus-v1")

def _normalize(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()

def check_span(pdf_name, page_num, span_text):
    doc = fitz.open(corpus_dir / pdf_name)
    page_text = _normalize(doc.load_page(page_num - 1).get_text())
    norm_span = _normalize(span_text)
    found = norm_span in page_text
    print(f"[{'PASS' if found else 'FAIL'}] {pdf_name} p.{page_num}: span len={len(norm_span)}")
    if not found:
        print(f"  Looking for: {repr(norm_span)}")
        print(f"  Page text was: {repr(page_text[:300])} ...")
    return found

tests = [
    # Q01
    ("10 RAG Architectures.pdf", 1, "A user query is embedded, relevant documents are retrieved from a vector database, and the LLM generates an answer grounded in that context."),
    # Q02
    ("10 RAG Architectures.pdf", 1, "The system behaves like an agent that can decide: ● what to retrieve ● whether to retrieve ● which tools to call ● how many steps to take"),
    # Q03
    ("10 RAG Architectures.pdf", 3, "It can: ● decide whether retrieval is needed ● critique retrieved documents ● refine or re-retrieve before answering"),
    # Q04
    ("10 RAG Architectures.pdf", 4, "The system adapts retrieval strategy based on query complexity."),
    ("10 RAG Architectures.pdf", 4, "Focuses on fixing bad retrievals. The system: ● detects irrelevant or low-quality documents ● filters or re-ranks them ● may re-query before answering"),
    # Q05
    ("10 RAG Architectures.pdf", 7, "Optimizes RAG pipelines under cost constraints (tokens, API calls, latency)."),
    ("10 RAG Architectures.pdf", 7, "Focuses on making RAG outputs explainable. The system: ● shows retrieved sources ● provides reasoning traces ● justifies answers with evidence"),
    ("10 RAG Architectures.pdf", 8, "Explains decision with cited rules and reasoning"),
    # Q06
    ("DBMS.pdf", 2, "DBMS helps in:\n1)\t\nDatabase design: It helps to decide how to organise the stored data.\n2)\t\nData analysis: It tells to execute queries over data in DBMS.\n3)\t\n Concurrency and robustness: DBMS allows multiple users to access \ndata concurrently and protects data in case of system failures.\n4)\t\n Efficiency and scalability: DBMS efficiently give answers to the \nqueries and the cost-effectiveness, ability to accommodate increased \nworkload and makes it scalable."),
    # Q07
    ("DBMS.pdf", 5, "Compound key: Key with multiple attributes/columns."),
    # Q08
    ("DBMS.pdf", 6, "Super-key: It’s a collection of one or more attributes that allow us to identify an entity in the relation uniquely. The superset of the candidate key is known as the super key in a relation."),
    ("DBMS.pdf", 8, "Candidate key: The minimal superkey is defined as the candidate key."),
    # Q09
    ("DBMS.pdf", 8, "Alternate Key: All other keys are alternate keys from the set of candidate keys, except the primary key."),
    # Q10
    ("DBMS.pdf", 8, "Entity integrity constraints:\n\t\ny\nEvery relation must have a primary key\n\t\ny\nEvery primary key must be unique\n\t\ny\nA primary key should not be NULL"),
    # Q11
    ("Operating-Systems.pdf", 6, "In uniprogramming system can execute only one program at once.\n\t\ny\nA lot of Wastage of CPU resources occurs here."),
    ("Operating-Systems.pdf", 7, "Multiprogramming came into the picture to overcome the shortcomings of Uniprogramming.\n\t\ny\nOperating system is able to manage multiple ready to run programs in memory at once."),
    # Q12
    ("Operating-Systems.pdf", 7, "In this case, the process currently running releases the CPU voluntarily:"),
    ("Operating-Systems.pdf", 8, "It allows forceful reallocation of the CPU from the current running process to another process from the process pool."),
    # Q13
    ("Operating-Systems.pdf", 9, "when an executing process needs I/O, it gets blocked and waits in I/O queue, by the time the operating system schedules other processes from the ready queue to execute on the CPU."),
    # Q14
    ("Operating-Systems.pdf", 10, "When a system has multiple processors, and they can be used to execute multiple instructions parallelly then it is known as multiprocessing. Hence multiple processes are required for multitasking while a single processor is needed to do multitasking."),
    # Q15
    ("Operating-Systems.pdf", 11, "Hard real time system:\nAn OS that works for those applications whose deadlines are very strict.\nExample: Satellite control"),
    ("Operating-Systems.pdf", 11, "Soft real time system:\nThese OS works for applications whose deadlines are narrow(less strict).\nReal Time OS works mainly on primary memory only.\nExample: Banking"),
]

all_pass = True
for pdf, page, text in tests:
    if not check_span(pdf, page, text):
        all_pass = False

print(f"\nFinal Result: {'ALL SPANS MATCH EXACTLY' if all_pass else 'SOME SPANS FAILED'}")
