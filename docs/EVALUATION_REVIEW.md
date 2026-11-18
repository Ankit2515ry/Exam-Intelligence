# Exam Intelligence — Pilot Dataset Human Review Sheet

**Dataset Version:** `pilot-v1`  
**Total Questions:** 15  
**Composition:** 13 Answerable, 2 Unanswerable  
**Current Status:** All 15 questions have been approved by human review (`APPROVED`).  
**Review Guideline:** Verify each question against the physical PDF page, the reference answer, the supporting passage, and the mapped indexed chunk ID before approving for retrieval evaluation.

---

## Summary Table

| QID | Document | Scope UUID | Page(s) | Category | Status | Mapped Chunk(s) | Reviewer Decision |
|:---:|---|---|:---:|---|:---:|---|:---:|
| **Q01** | `10 RAG Architectures.pdf` | `cbd60b93-0e2b-4e19-b8ad-d63461eac601` | 1 | `direct_factual` | Answerable | `7aab5876...` (c0) | **APPROVED** |
| **Q02** | `10 RAG Architectures.pdf` | `cbd60b93-0e2b-4e19-b8ad-d63461eac601` | 1 | `paraphrased_semantic` | Answerable | `e02d9b03...` (c3) | **APPROVED** |
| **Q03** | `10 RAG Architectures.pdf` | `cbd60b93-0e2b-4e19-b8ad-d63461eac601` | 3 | `direct_factual` | Answerable | `cb1960ec...` (c11) | **APPROVED** |
| **Q04** | `10 RAG Architectures.pdf` | `cbd60b93-0e2b-4e19-b8ad-d63461eac601` | 4 | `multi_step_reasoning` | Answerable | `302dc9d4...` (c14), `efa5f756...` (c17) | **APPROVED** |
| **Q05** | `10 RAG Architectures.pdf` | `cbd60b93-0e2b-4e19-b8ad-d63461eac601` | N/A | `unanswerable` | **Unanswerable** | None (Abstention) | **APPROVED** |
| **Q06** | `DBMS.pdf` | `f513d63e-e487-4d83-b40a-af81169662de` | 2 | `direct_factual` | Answerable | `f8913c75...` (c4), `342a61df...` (c5), `a5d69738...` (c6) | **APPROVED** |
| **Q07** | `DBMS.pdf` | `f513d63e-e487-4d83-b40a-af81169662de` | 5 | `direct_factual` | Answerable | `5a761b29...` (c20) | **APPROVED** |
| **Q08** | `DBMS.pdf` | `f513d63e-e487-4d83-b40a-af81169662de` | 6, 8 | `multi_step_reasoning` | Answerable | `2ea0f07c...` (c27), `8738ff54...` (c35) | **APPROVED** |
| **Q09** | `DBMS.pdf` | `f513d63e-e487-4d83-b40a-af81169662de` | 8 | `direct_factual` | Answerable | `96a24c77...` (c37) | **APPROVED** |
| **Q10** | `DBMS.pdf` | `f513d63e-e487-4d83-b40a-af81169662de` | N/A | `unanswerable` | **Unanswerable** | None (Abstention) | **APPROVED** |
| **Q11** | `Operating-Systems.pdf` | `6c04513a-30bd-4fea-814c-9f07c1e9c0b7` | 6, 7 | `multi_step_reasoning` | Answerable | `a7ec725b...` (c36), `b966b6b3...` (c39) | **APPROVED** |
| **Q12** | `Operating-Systems.pdf` | `6c04513a-30bd-4fea-814c-9f07c1e9c0b7` | 7, 8 | `paraphrased_semantic` | Answerable | `48450d43...` (c42), `2a0e1a31...` (c45) | **APPROVED** |
| **Q13** | `Operating-Systems.pdf` | `6c04513a-30bd-4fea-814c-9f07c1e9c0b7` | 9 | `direct_factual` | Answerable | `53fd037e...` (c59) | **APPROVED** |
| **Q14** | `Operating-Systems.pdf` | `6c04513a-30bd-4fea-814c-9f07c1e9c0b7` | 10 | `multi_step_reasoning` | Answerable | `29774bbd...` (c63), `f07b9b65...` (c64) | **APPROVED** |
| **Q15** | `Operating-Systems.pdf` | `6c04513a-30bd-4fea-814c-9f07c1e9c0b7` | 11 | `direct_factual` | Answerable | `3ba26293...` (c70), `6dbeb141...` (c72) | **APPROVED** |

---

## Detailed Question Review Records

### Q01
- **Exact Question:** In Standard RAG, what are the main steps from the user query to the generated answer?
- **Document Filename:** `10 RAG Architectures.pdf`
- **Document UUID:** `cbd60b93-0e2b-4e19-b8ad-d63461eac601`
- **Physical Page Number(s):** 1
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** Embed the query, retrieve relevant documents from a vector database, and have the LLM generate an answer using the retrieved context.
- **Supporting Passage(s):**
  > "A user query is embedded, relevant documents are retrieved from a vector database, and the LLM generates an answer grounded in that context"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `0` | Chunk ID: `7aab5876-0f7f-43f1-b92c-e35fbb96cf34`
- **Reviewer Decision:** **APPROVED**

---

### Q02
- **Exact Question:** How does Agentic RAG differ from the Standard RAG pipeline?
- **Document Filename:** `10 RAG Architectures.pdf`
- **Document UUID:** `cbd60b93-0e2b-4e19-b8ad-d63461eac601`
- **Physical Page Number(s):** 1
- **Status:** Answerable (`category: paraphrased_semantic`)
- **Reference Answer:** Agentic RAG makes iterative decisions about whether and what to retrieve, which tools to call, and how many steps to perform; Standard RAG follows a basic retrieval-and-generation pass.
- **Supporting Passage(s):**
  > "The system behaves like an agent that can decide: ● what to retrieve ● whether to retrieve ● which tools to call ● how many steps to take"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `3` | Chunk ID: `e02d9b03-52aa-4d2c-880c-939e6a20b8f4`
- **Reviewer Decision:** **APPROVED**

---

### Q03
- **Exact Question:** What three actions can Self RAG take to evaluate its own retrieval and output?
- **Document Filename:** `10 RAG Architectures.pdf`
- **Document UUID:** `cbd60b93-0e2b-4e19-b8ad-d63461eac601`
- **Physical Page Number(s):** 3
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** Decide whether retrieval is needed, critique retrieved documents, and refine or re-retrieve before answering.
- **Supporting Passage(s):**
  > "It can: ● decide whether retrieval is needed ● critique retrieved documents ● refine or re-retrieve before answering"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `11` | Chunk ID: `cb1960ec-2d17-48f5-a6e5-4a69cf4f44c4`
- **Reviewer Decision:** **APPROVED**

---

### Q04
- **Exact Question:** How do Adaptive RAG and Corrective RAG differ in their primary goals?
- **Document Filename:** `10 RAG Architectures.pdf`
- **Document UUID:** `cbd60b93-0e2b-4e19-b8ad-d63461eac601`
- **Physical Page Number(s):** 4
- **Status:** Answerable (`category: multi_step_reasoning`)
- **Reference Answer:** Adaptive RAG chooses retrieval depth based on query complexity; Corrective RAG detects and fixes poor retrieval by filtering, re-ranking, or re-querying.
- **Supporting Passage(s):**
  1. (Page 4): > "The system adapts retrieval strategy based on query complexity."
  2. (Page 4): > "Focuses on fixing bad retrievals. The system: ● detects irrelevant or low-quality documents ● filters or re-ranks them ● may re-query before answering"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `14` | Chunk ID: `302dc9d4-1a6f-4220-af8e-e31b6727284b`
  - Chunk Index: `17` | Chunk ID: `efa5f756-3c07-449e-b248-be589c313137`
- **Reviewer Decision:** **APPROVED**

---

### Q05
- **Exact Question:** What was Google's worldwide Gemini API revenue in 2025?
- **Document Filename:** `10 RAG Architectures.pdf`
- **Document UUID:** `cbd60b93-0e2b-4e19-b8ad-d63461eac601`
- **Physical Page Number(s):** N/A (entire 8-page document evaluated)
- **Status:** **Unanswerable** (`category: unanswerable`)
- **Reference Answer:** `null` (System expected behavior: state that the uploaded document does not provide this information)
- **Supporting Passage(s):** `[]` (none)
- **Relevant Indexed Chunk(s):** `[]` (none)
- **Verification Method:** Full-text scan across all 8 pages of `10 RAG Architectures.pdf` confirmed zero occurrences of "Gemini", "Google", "worldwide", or "2025". The document strictly describes 10 architectural RAG patterns with no financial or revenue metrics.
- **Reviewer Decision:** **APPROVED**

---

### Q06
- **Exact Question:** What four areas does the DBMS introduction say a DBMS helps with?
- **Document Filename:** `DBMS.pdf`
- **Document UUID:** `f513d63e-e487-4d83-b40a-af81169662de`
- **Physical Page Number(s):** 2
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** Database design, data analysis, concurrency and robustness, and efficiency and scalability.
- **Supporting Passage(s):**
  1. (Page 2): > "DBMS helps in: 1) Database design: It helps to decide how to organise the stored data. 2) Data analysis: It tells to execute queries over data in DBMS"
  2. (Page 2): > "Concurrency and robustness: DBMS allows multiple users to access data concurrently and protects data in case of system failures"
  3. (Page 2): > "Efficiency and scalability: DBMS efficiently give answers to the queries and the cost-effectiveness, ability to accommodate increased workload and makes it scalable"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `4` | Chunk ID: `f8913c75-b6d8-4bc2-841f-a36a5927ad99`
  - Chunk Index: `5` | Chunk ID: `342a61df-c148-4cb9-92c2-843c0d68f6eb`
  - Chunk Index: `6` | Chunk ID: `a5d69738-d65e-4db9-8b6b-db72be885d58`
- **Reviewer Decision:** **APPROVED**

---

### Q07
- **Exact Question:** What is a compound key according to the DBMS notes?
- **Document Filename:** `DBMS.pdf`
- **Document UUID:** `f513d63e-e487-4d83-b40a-af81169662de`
- **Physical Page Number(s):** 5
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** A key composed of multiple attributes or columns.
- **Supporting Passage(s):**
  > "Compound key: Key with multiple attributes/columns."
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `20` | Chunk ID: `5a761b29-e0dc-49ef-b4b4-7b0a703d98eb`
- **Reviewer Decision:** **APPROVED**

---

### Q08
- **Exact Question:** How is a candidate key different from a superkey?
- **Document Filename:** `DBMS.pdf`
- **Document UUID:** `f513d63e-e487-4d83-b40a-af81169662de`
- **Physical Page Number(s):** 6, 8
- **Status:** Answerable (`category: multi_step_reasoning`)
- **Reference Answer:** A candidate key is a minimal superkey; a superkey is any collection of attributes that uniquely identifies a tuple, including supersets of candidate keys.
- **Supporting Passage(s):**
  1. (Page 6): > "Super-key: It’s a collection of one or more attributes that allow us to identify an entity in the relation uniquely."
  2. (Page 8): > "Candidate key: The minimal superkey is defined as the candidate key."
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `27` | Chunk ID: `2ea0f07c-3f48-4e89-be27-31a89c49ca24`
  - Chunk Index: `35` | Chunk ID: `8738ff54-d890-482a-a92c-623b036cb562`
- **Reviewer Decision:** **APPROVED**

---

### Q09
- **Exact Question:** What are alternate keys?
- **Document Filename:** `DBMS.pdf`
- **Document UUID:** `f513d63e-e487-4d83-b40a-af81169662de`
- **Physical Page Number(s):** 8
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** Candidate keys that are not selected as the primary key.
- **Supporting Passage(s):**
  > "Alternate Key: All other keys are alternate keys from the set of candidate keys, except the primary key"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `37` | Chunk ID: `96a24c77-4a00-47d2-97cf-8924ee26ffda`
- **Reviewer Decision:** **APPROVED**

---

### Q10
- **Exact Question:** What are the MongoDB replica-set election rules?
- **Document Filename:** `DBMS.pdf`
- **Document UUID:** `f513d63e-e487-4d83-b40a-af81169662de`
- **Physical Page Number(s):** N/A (entire 231-page document evaluated)
- **Status:** **Unanswerable** (`category: unanswerable`)
- **Reference Answer:** `null` (System expected behavior: state that the uploaded document does not provide this information)
- **Supporting Passage(s):** `[]` (none)
- **Relevant Indexed Chunk(s):** `[]` (none)
- **Verification Method:** Full-text scan across all 231 pages of `DBMS.pdf` (204,220 characters) confirmed zero occurrences of "mongo", "mongodb", "replica", "quorum", "consensus", "raft", "paxos", or "nosql". The document is strictly an introduction to relational database systems (ER modeling, relational algebra, SQL DDL/DML, normalization up to BCNF, transactions, and 2PL concurrency).
- **Reviewer Decision:** **APPROVED**

---

### Q11
- **Exact Question:** Why was multiprogramming introduced as an improvement over uniprogramming?
- **Document Filename:** `Operating-Systems.pdf`
- **Document UUID:** `6c04513a-30bd-4fea-814c-9f07c1e9c0b7`
- **Physical Page Number(s):** 6, 7
- **Status:** Answerable (`category: multi_step_reasoning`)
- **Reference Answer:** Uniprogramming runs only one program and wastes CPU resources; multiprogramming manages multiple ready-to-run programs in memory and can keep the CPU better utilized.
- **Supporting Passage(s):**
  1. (Page 6): > "In uniprogramming system can execute only one program at once"
  2. (Page 7): > "Multiprogramming came into the picture to overcome the shortcomings of Uniprogramming. y Operating system is able to manage multiple ready to run programs in memory at once"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `36` | Chunk ID: `a7ec725b-9d48-4cb1-9877-bbccfbb90453`
  - Chunk Index: `39` | Chunk ID: `b966b6b3-da6f-42a9-b220-410a6a02b173`
- **Reviewer Decision:** **APPROVED**

---

### Q12
- **Exact Question:** What distinguishes non-preemptive from preemptive multiprogramming?
- **Document Filename:** `Operating-Systems.pdf`
- **Document UUID:** `6c04513a-30bd-4fea-814c-9f07c1e9c0b7`
- **Physical Page Number(s):** 7, 8
- **Status:** Answerable (`category: paraphrased_semantic`)
- **Reference Answer:** In non-preemptive scheduling the running process releases the CPU voluntarily; preemptive scheduling allows the OS to forcibly reallocate the CPU.
- **Supporting Passage(s):**
  1. (Page 7): > "In this case, the process currently running releases the CPU voluntarily:"
  2. (Page 8): > "It allows forceful reallocation of the CPU from the current running process to another process from the process pool"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `42` | Chunk ID: `48450d43-0797-4e67-857c-fbf94943fcf4`
  - Chunk Index: `45` | Chunk ID: `2a0e1a31-a06d-4950-8b17-094132ef478d`
- **Reviewer Decision:** **APPROVED**

---

### Q13
- **Exact Question:** What happens in a multiprogramming OS while one process is waiting for an I/O operation?
- **Document Filename:** `Operating-Systems.pdf`
- **Document UUID:** `6c04513a-30bd-4fea-814c-9f07c1e9c0b7`
- **Physical Page Number(s):** 9
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** The blocked process waits in the I/O queue while the OS schedules another ready process on the CPU.
- **Supporting Passage(s):**
  > "In this multiprogramming environment, when an executing process needs I/O, it gets blocked and waits in I/O queue, by the time the operating system schedules other processes from the ready queue to execute on the CPU"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `59` | Chunk ID: `53fd037e-a035-4ae0-a226-c2aafebe1fa6`
- **Reviewer Decision:** **APPROVED**

---

### Q14
- **Exact Question:** What distinguishes multitasking from multiprocessing in the provided notes?
- **Document Filename:** `Operating-Systems.pdf`
- **Document UUID:** `6c04513a-30bd-4fea-814c-9f07c1e9c0b7`
- **Physical Page Number(s):** 10
- **Status:** Answerable (`category: multi_step_reasoning`)
- **Reference Answer:** Multitasking rapidly switches among tasks, potentially on one processor; multiprocessing uses multiple processors to execute instructions in parallel.
- **Supporting Passage(s):**
  1. (Page 10): > "When a system has multiple processors, and they can be used to execute multiple instructions parallelly then it is known as multiprocessing"
  2. (Page 10): > "Hence multiple processes are required for multitasking while a single processor is needed to do multitasking"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `63` | Chunk ID: `29774bbd-986c-4f11-9a4f-560bb3c27616`
  - Chunk Index: `64` | Chunk ID: `f07b9b65-680c-4fa6-848e-289db5b75017`
- **Reviewer Decision:** **APPROVED**

---

### Q15
- **Exact Question:** Give one example of a hard real-time system and one of a soft real-time system from the notes.
- **Document Filename:** `Operating-Systems.pdf`
- **Document UUID:** `6c04513a-30bd-4fea-814c-9f07c1e9c0b7`
- **Physical Page Number(s):** 11
- **Status:** Answerable (`category: direct_factual`)
- **Reference Answer:** Hard real-time: satellite control; soft real-time: banking.
- **Supporting Passage(s):**
  1. (Page 11): > "Hard real time system: An OS that works for those applications whose deadlines are very strict"
  2. (Page 11): > "Example: Banking Advantages of real time os: Error free"
- **Relevant Indexed Chunk(s):**
  - Chunk Index: `70` | Chunk ID: `3ba26293-181d-400d-9445-56fa08a46cf4`
  - Chunk Index: `72` | Chunk ID: `6dbeb141-893d-4c3e-8cba-c49bcfca3c09`
- **Reviewer Decision:** **APPROVED**
