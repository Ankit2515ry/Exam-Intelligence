"""
Generate backend/evaluation/private/pilot-v1.json with:
- 13 answerable questions (verified against pages and chunks)
- 2 unanswerable questions (Q05 and Q10, verified across full document scopes)
"""
import json
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from app.evaluation.dataset import validate_dataset
from app.evaluation.corpus import validate_pilot

rag_uuid = "cbd60b93-0e2b-4e19-b8ad-d63461eac601"
dbms_uuid = "f513d63e-e487-4d83-b40a-af81169662de"
os_uuid = "6c04513a-30bd-4fea-814c-9f07c1e9c0b7"

records = [
    {
        "question_id": "Q01",
        "question": "In Standard RAG, what are the main steps from the user query to the generated answer?",
        "document_scope_uuid": rag_uuid,
        "expected_answer": "Embed the query, retrieve relevant documents from a vector database, and have the LLM generate an answer using the retrieved context.",
        "answerable": True,
        "relevant_document_ids": [rag_uuid],
        "relevant_page_numbers": [1],
        "supporting_spans": [
            {
                "document_id": rag_uuid,
                "page": 1,
                "text": "A user query is embedded, relevant documents are retrieved from a vector database, and the LLM generates an answer grounded in that context"
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against 10 RAG Architectures.pdf page 1 and chunk index 0; pending human review."
    },
    {
        "question_id": "Q02",
        "question": "How does Agentic RAG differ from the Standard RAG pipeline?",
        "document_scope_uuid": rag_uuid,
        "expected_answer": "Agentic RAG makes iterative decisions about whether and what to retrieve, which tools to call, and how many steps to perform; Standard RAG follows a basic retrieval-and-generation pass.",
        "answerable": True,
        "relevant_document_ids": [rag_uuid],
        "relevant_page_numbers": [1],
        "supporting_spans": [
            {
                "document_id": rag_uuid,
                "page": 1,
                "text": "The system behaves like an agent that can decide: ●\u200b what to retrieve ●\u200b whether to retrieve ●\u200b which tools to call ●\u200b how many steps to take"
            }
        ],
        "category": "paraphrased_semantic",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against 10 RAG Architectures.pdf page 1 and chunk index 3; pending human review."
    },
    {
        "question_id": "Q03",
        "question": "What three actions can Self RAG take to evaluate its own retrieval and output?",
        "document_scope_uuid": rag_uuid,
        "expected_answer": "Decide whether retrieval is needed, critique retrieved documents, and refine or re-retrieve before answering.",
        "answerable": True,
        "relevant_document_ids": [rag_uuid],
        "relevant_page_numbers": [3],
        "supporting_spans": [
            {
                "document_id": rag_uuid,
                "page": 3,
                "text": "It can: ●\u200b decide whether retrieval is needed ●\u200b critique retrieved documents ●\u200b refine or re-retrieve before answering"
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against 10 RAG Architectures.pdf page 3 and chunk index 11; pending human review."
    },
    {
        "question_id": "Q04",
        "question": "How do Adaptive RAG and Corrective RAG differ in their primary goals?",
        "document_scope_uuid": rag_uuid,
        "expected_answer": "Adaptive RAG chooses retrieval depth based on query complexity; Corrective RAG detects and fixes poor retrieval by filtering, re-ranking, or re-querying.",
        "answerable": True,
        "relevant_document_ids": [rag_uuid],
        "relevant_page_numbers": [4],
        "supporting_spans": [
            {
                "document_id": rag_uuid,
                "page": 4,
                "text": "The system adapts retrieval strategy based on query complexity."
            },
            {
                "document_id": rag_uuid,
                "page": 4,
                "text": "Focuses on fixing bad retrievals.\u200b The system:\n●\u200b detects irrelevant or low-quality documents\n●\u200b filters or re-ranks them\n●\u200b may re-query before answering"
            }
        ],
        "category": "multi_step_reasoning",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against 10 RAG Architectures.pdf page 4 and chunks 14 & 17; pending human review."
    },
    {
        "question_id": "Q05",
        "question": "What was Google's worldwide Gemini API revenue in 2025?",
        "document_scope_uuid": rag_uuid,
        "expected_answer": None,
        "answerable": False,
        "relevant_document_ids": [],
        "relevant_page_numbers": [],
        "supporting_spans": [],
        "category": "unanswerable",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified unanswerable across complete document scope of 10 RAG Architectures.pdf (8 pages, 0 occurrences of Gemini/Google API revenue); expected behavior is abstention; pending human review."
    },
    {
        "question_id": "Q06",
        "question": "What four areas does the DBMS introduction say a DBMS helps with?",
        "document_scope_uuid": dbms_uuid,
        "expected_answer": "Database design, data analysis, concurrency and robustness, and efficiency and scalability.",
        "answerable": True,
        "relevant_document_ids": [dbms_uuid],
        "relevant_page_numbers": [2],
        "supporting_spans": [
            {
                "document_id": dbms_uuid,
                "page": 2,
                "text": "DBMS helps in: 1) Database design: It helps to decide how to organise the stored data. 2) Data analysis: It tells to execute queries over data in DBMS"
            },
            {
                "document_id": dbms_uuid,
                "page": 2,
                "text": "Concurrency and robustness: DBMS allows multiple users to access data concurrently and protects data in case of system failures"
            },
            {
                "document_id": dbms_uuid,
                "page": 2,
                "text": "Efficiency and scalability: DBMS efficiently give answers to the queries and the cost-effectiveness, ability to accommodate increased workload and makes it scalable"
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against DBMS.pdf page 2 and chunks 4, 5, 6; pending human review."
    },
    {
        "question_id": "Q07",
        "question": "What is a compound key according to the DBMS notes?",
        "document_scope_uuid": dbms_uuid,
        "expected_answer": "A key composed of multiple attributes or columns.",
        "answerable": True,
        "relevant_document_ids": [dbms_uuid],
        "relevant_page_numbers": [5],
        "supporting_spans": [
            {
                "document_id": dbms_uuid,
                "page": 5,
                "text": "Compound key: Key with multiple attributes/columns."
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against DBMS.pdf page 5 and chunk 20; pending human review."
    },
    {
        "question_id": "Q08",
        "question": "How is a candidate key different from a superkey?",
        "document_scope_uuid": dbms_uuid,
        "expected_answer": "A candidate key is a minimal superkey; a superkey is any collection of attributes that uniquely identifies a tuple, including supersets of candidate keys.",
        "answerable": True,
        "relevant_document_ids": [dbms_uuid],
        "relevant_page_numbers": [6, 8],
        "supporting_spans": [
            {
                "document_id": dbms_uuid,
                "page": 6,
                "text": "Super-key: It’s a collection of one or more attributes that allow us to identify an entity in the relation uniquely."
            },
            {
                "document_id": dbms_uuid,
                "page": 8,
                "text": "Candidate key: The minimal superkey is defined as the candidate key."
            }
        ],
        "category": "multi_step_reasoning",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against DBMS.pdf pages 6 & 8 and chunks 27 & 35; pending human review."
    },
    {
        "question_id": "Q09",
        "question": "What are alternate keys?",
        "document_scope_uuid": dbms_uuid,
        "expected_answer": "Candidate keys that are not selected as the primary key.",
        "answerable": True,
        "relevant_document_ids": [dbms_uuid],
        "relevant_page_numbers": [8],
        "supporting_spans": [
            {
                "document_id": dbms_uuid,
                "page": 8,
                "text": "Alternate Key: All other keys are alternate keys from the set of candidate keys, except the primary key"
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against DBMS.pdf page 8 and chunk 37; pending human review."
    },
    {
        "question_id": "Q10",
        "question": "What are the MongoDB replica-set election rules?",
        "document_scope_uuid": dbms_uuid,
        "expected_answer": None,
        "answerable": False,
        "relevant_document_ids": [],
        "relevant_page_numbers": [],
        "supporting_spans": [],
        "category": "unanswerable",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified unanswerable across complete document scope of DBMS.pdf (231 pages, covers only relational DBMS; 0 mentions of MongoDB or replica sets); expected behavior is abstention; pending human review."
    },
    {
        "question_id": "Q11",
        "question": "Why was multiprogramming introduced as an improvement over uniprogramming?",
        "document_scope_uuid": os_uuid,
        "expected_answer": "Uniprogramming runs only one program and wastes CPU resources; multiprogramming manages multiple ready-to-run programs in memory and can keep the CPU better utilized.",
        "answerable": True,
        "relevant_document_ids": [os_uuid],
        "relevant_page_numbers": [6, 7],
        "supporting_spans": [
            {
                "document_id": os_uuid,
                "page": 6,
                "text": "In uniprogramming system can execute only one program at once"
            },
            {
                "document_id": os_uuid,
                "page": 7,
                "text": "Multiprogramming came into the picture to overcome the shortcomings of Uniprogramming. y Operating system is able to manage multiple ready to run programs in memory at once"
            }
        ],
        "category": "multi_step_reasoning",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against Operating-Systems.pdf pages 6 & 7 and chunks 36 & 39; pending human review."
    },
    {
        "question_id": "Q12",
        "question": "What distinguishes non-preemptive from preemptive multiprogramming?",
        "document_scope_uuid": os_uuid,
        "expected_answer": "In non-preemptive scheduling the running process releases the CPU voluntarily; preemptive scheduling allows the OS to forcibly reallocate the CPU.",
        "answerable": True,
        "relevant_document_ids": [os_uuid],
        "relevant_page_numbers": [7, 8],
        "supporting_spans": [
            {
                "document_id": os_uuid,
                "page": 7,
                "text": "In this case, the process currently running releases the CPU voluntarily:"
            },
            {
                "document_id": os_uuid,
                "page": 8,
                "text": "It allows forceful reallocation of the CPU from the current running process to another process from the process pool"
            }
        ],
        "category": "paraphrased_semantic",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against Operating-Systems.pdf pages 7 & 8 and chunks 42 & 45; pending human review."
    },
    {
        "question_id": "Q13",
        "question": "What happens in a multiprogramming OS while one process is waiting for an I/O operation?",
        "document_scope_uuid": os_uuid,
        "expected_answer": "The blocked process waits in the I/O queue while the OS schedules another ready process on the CPU.",
        "answerable": True,
        "relevant_document_ids": [os_uuid],
        "relevant_page_numbers": [9],
        "supporting_spans": [
            {
                "document_id": os_uuid,
                "page": 9,
                "text": "In this multiprogramming environment, when an executing process needs I/O, it gets blocked and waits in I/O queue, by the time the operating system schedules other processes from the ready queue to execute on the CPU"
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against Operating-Systems.pdf page 9 and chunk 59; pending human review."
    },
    {
        "question_id": "Q14",
        "question": "What distinguishes multitasking from multiprocessing in the provided notes?",
        "document_scope_uuid": os_uuid,
        "expected_answer": "Multitasking rapidly switches among tasks, potentially on one processor; multiprocessing uses multiple processors to execute instructions in parallel.",
        "answerable": True,
        "relevant_document_ids": [os_uuid],
        "relevant_page_numbers": [10],
        "supporting_spans": [
            {
                "document_id": os_uuid,
                "page": 10,
                "text": "When a system has multiple processors, and they can be used to execute multiple instructions parallelly then it is known as multiprocessing"
            },
            {
                "document_id": os_uuid,
                "page": 10,
                "text": "Hence multiple processes are required for multitasking while a single processor is needed to do multitasking"
            }
        ],
        "category": "multi_step_reasoning",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against Operating-Systems.pdf page 10 and chunks 63 & 64; pending human review."
    },
    {
        "question_id": "Q15",
        "question": "Give one example of a hard real-time system and one of a soft real-time system from the notes.",
        "document_scope_uuid": os_uuid,
        "expected_answer": "Hard real-time: satellite control; soft real-time: banking.",
        "answerable": True,
        "relevant_document_ids": [os_uuid],
        "relevant_page_numbers": [11],
        "supporting_spans": [
            {
                "document_id": os_uuid,
                "page": 11,
                "text": "Hard real time system: An OS that works for those applications whose deadlines are very strict"
            },
            {
                "document_id": os_uuid,
                "page": 11,
                "text": "Example: Banking Advantages of real time os: Error free"
            }
        ],
        "category": "direct_factual",
        "ocr_scanned": False,
        "mathematical": False,
        "reviewer_status": "draft",
        "reviewer_notes": "Verified against Operating-Systems.pdf page 11 and chunks 70 & 72; pending human review."
    }
]

pilot_dataset = {
    "dataset_version": "pilot-v1",
    "records": records
}

target_path = backend_dir / "evaluation" / "private" / "pilot-v1.json"
target_path.write_text(json.dumps(pilot_dataset, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(records)} records to {target_path}")

validate_dataset(records, require_approved=False)
print("validate_dataset: PASS")

selection_path = backend_dir / "evaluation" / "private" / "corpus-v1-selection.json"
selection_manifest = json.loads(selection_path.read_text(encoding="utf-8"))
corpus_dir = backend_dir / "evaluation" / "corpus" / "corpus-v1"

report = validate_pilot(records, selection_manifest, corpus_dir)
print("\nvalidate_pilot REPORT:")
print(json.dumps(report, indent=2))
