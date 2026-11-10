"""
Main FastAPI Application

Responsibilities:
-----------------
1. Create FastAPI app
2. Register API routers
3. Configure middleware
4. Configure metadata

IMPORTANT:
-----------
This file should remain lightweight.

It should NOT contain:
----------------------
- retrieval logic
- ingestion logic
- vector DB operations
- prompt engineering
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI

import app.db.models

from fastapi.middleware.cors import (
    CORSMiddleware
)


# =========================================================
# IMPORT ROUTERS
# =========================================================

from app.api.upload import (
    router as upload_router
)

from app.api.chat import (
    router as chat_router
)

from app.auth.routes import (
    router as auth_router
)
from app.api.health import (
    router as health_router
)
# import shutil
'''
shutil Python ki standard library ka module hai.
Iska use file aur directory operations ke liye hota hai.
'''
#  print("TESSERACT PATH =", shutil.which("tesseract"))

# =========================================================
# CREATE FASTAPI APP
# =========================================================
# print("step 1: Creating FastAPI app")
logger.info("Creating FastAPI app")
app = FastAPI(

    title="Exam Intelligence API",

    version="1.0.0",

    description=(
        "AI-Powered Exam Preparation "
        "and RAG System"
    )
)

# print("step 2: FastAPI app created successfully")
logger.info("FastAPI app created")
# =========================================================
# CORS MIDDLEWARE
# =========================================================
# print("step 3: Configuring CORS middleware")
logger.info("Configuring CORS middleware")
app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)
# print("step 4: CORS middleware configured successfully")
logger.info("CORS middleware configured")
# app.add_middleware(

#     CORSMiddleware,
#     allow_origins=[
#         "http://your-frontend.vercel.app"
#     ],
#     allow_credentials=True,

#     allow_methods=["*"],

#     allow_headers=["*"],
# )


# =========================================================
# REGISTER ROUTERS
# =========================================================
# print("step 5: Registering API routers")
logger.info("Registering API routers")
app.include_router(
    upload_router
)
# print("step 6: API routers registered successfully")
logger.info("Upload router registered")
app.include_router(
    chat_router
)
# print("step 7: Chat router registered successfully")
logger.info("Chat router registered")

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"]
)

# print("step 8: Auth router registered successfully")
logger.info("Authentication router registered")
app.include_router(health_router)
logger.info("Health router registered")
# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    """
    Informational root endpoint.

    Use /health/live and /health/ready for health probes.
    """

    return {

        "message": (
            "Exam Intelligence API Running"
        ),

        "status": "running"
    }
'''
Liveness
Readiness
Tests and smoke checks 
'''
# print("step 9: Health check endpoint configured successfully")
logger.info("Application routes configured")



"""
=========================================================
MAIN.PY - COMPLETE UNDERSTANDING SUMMARY
=========================================================

1. ROLE OF MAIN.PY
------------------
- main.py is the main entry point of the backend application.
- It acts as the central configuration and assembly point.
- It connects different components of the application.
- It should contain application setup, not business logic.
- It follows the Separation of Concerns principle.

2. PYTHON IMPORTS
-----------------
- Imports allow us to use functionality from other modules
  and libraries.
- FastAPI is imported to create the backend application.
- Database models are imported so their definitions can
  be loaded into the application's ORM registry.
- CORSMiddleware is imported to configure CORS.
- Upload, Chat and Authentication routers are imported
  from their respective modules.

3. FASTAPI APPLICATION CREATION
-------------------------------
- FastAPI is a Python web framework used to build APIs.
- FastAPI is a class.
- app = FastAPI() creates an instance of that class.
- The app object represents the backend application.
- The app variable is referenced by Uvicorn to run the app.

4. FASTAPI METADATA
-------------------
- title: Defines the API application name.
- version: Specifies the API version.
- description: Provides information about the API.
- This metadata appears in generated API documentation.

5. UVICORN AND ASGI
-------------------
- Uvicorn is an ASGI server used to run FastAPI applications.
- ASGI stands for Asynchronous Server Gateway Interface.
- Uvicorn receives HTTP requests and forwards them to
  the FastAPI application.
- Example command: uvicorn app.main:app --reload
- app.main refers to the Python module.
- The final app refers to the FastAPI application object.
- --reload automatically restarts the server when code changes
  during development.

6. MIDDLEWARE
-------------
- Middleware processes requests and responses.
- It provides common functionality across multiple endpoints.
- Examples: CORS, logging and request processing.

7. CORS
-------
- CORS stands for Cross-Origin Resource Sharing.
- It is a browser security mechanism.
- It controls whether a frontend from one origin can access
  resources from a backend on another origin.
- CORSMiddleware handles CORS configuration in FastAPI.

CORS PARAMETERS:
- allow_origins: Specifies allowed frontend origins.
- allow_credentials: Controls credential support.
- allow_methods: Specifies allowed HTTP methods.
- allow_headers: Specifies allowed request headers.

- Wildcard (*) means all origins, methods or headers,
  depending on the parameter.
- Production applications should use explicitly trusted
  frontend origins.
- CORS is not authentication or authorization.

8. API ROUTERS
--------------
- APIRouter organizes related API endpoints into modules.
- Separate routers improve code organization and maintenance.
- Exam Intelligence uses:
    a. Upload Router - PDF upload functionality.
    b. Chat Router - Question-answer functionality.
    c. Auth Router - Authentication functionality.

- Importing a router makes its object available.
- app.include_router() registers its endpoints with the
  main FastAPI application.

9. ROUTER PREFIX AND TAGS
-------------------------
- prefix adds a common URL path to all endpoints of a router.
- Router-level and application-level prefixes combine.
- Duplicate prefixes can create unintended URLs.
- tags group endpoints in Swagger documentation.
- Tags do not provide endpoint security.

10. HEALTH CHECK ENDPOINT
-------------------------
- @app.get("/") registers an HTTP GET endpoint at the root.
- A decorator connects a Python function with an API route.
- The home() function handles requests to GET /.
- It returns a Python dictionary.
- FastAPI converts the dictionary into a JSON response.
- The current health check verifies basic responsiveness only.
- It does not verify database, vector database or LLM health.

11. HTTP AND JSON
-----------------
- HTTP stands for HyperText Transfer Protocol.
- It enables communication between clients and servers.
- GET: Retrieve data.
- POST: Submit or create data.
- PUT: Update a resource.
- PATCH: Partially update a resource.
- DELETE: Delete a resource.
- JSON stands for JavaScript Object Notation.
- JSON is commonly used for exchanging data between
  frontend and backend applications.

12. LOGGING AND DEBUGGING
-------------------------
- print() statements display execution messages in terminal.
- They help during development and debugging.
- Python logging is generally preferred for production.
- Logging supports levels such as INFO, WARNING and ERROR.

13. ARCHITECTURAL RESPONSIBILITIES
----------------------------------
main.py SHOULD:
- Create the FastAPI application.
- Configure application metadata.
- Register middleware.
- Register API routers.
- Configure global application behavior.
- Define simple root or health endpoints.

main.py SHOULD NOT:
- Perform PDF text extraction.
- Implement document chunking.
- Generate embeddings.
- Perform vector database operations.
- Implement retrieval logic.
- Construct prompts.
- Make LLM generation calls.
- Contain complex business logic.

14. IMPORTANT ARCHITECTURAL CONCEPT
-----------------------------------
- Separation of Concerns means keeping different
  responsibilities in separate modules.
- main.py connects components.
- Other modules implement their respective functionality.

=========================================================
END OF MAIN.PY SUMMARY
=========================================================
"""


"""
=========================================================
PYTHON MODULES, PACKAGES AND IMPORT SYSTEM
=========================================================

1. MODULAR PROGRAMMING
----------------------
- Modular programming divides a large application into
  smaller and manageable components.
- It improves readability, reusability and maintainability.
- It makes debugging and code management easier.

2. PYTHON MODULE
----------------
- A Python module is a .py file containing Python code.
- It can contain functions, classes and variables.
- Modules allow code to be reused across different files.
- Example: main.py, upload.py, chat.py.

3. PYTHON PACKAGE
-----------------
- A package organizes related Python modules into directories.
- Packages help structure large Python applications.
- A package can contain modules and subpackages.
- __init__.py is commonly used to define and initialize
  traditional Python packages.
- Modern namespace packages can exist without __init__.py.

4. MODULE VS PACKAGE
--------------------
- Module = Individual Python file.
- Package = Directory-based organization of modules.
- Example module: upload.py.
- Example package: app.api.

5. PYTHON IMPORT SYSTEM
-----------------------
- Import statements allow us to access code from other modules.
- Python locates, loads and executes a module when imported.
- Module-level statements execute during the first import.
- Loaded modules are tracked in sys.modules.
- Repeated imports normally reuse the cached module.

6. DIFFERENT IMPORT METHODS
---------------------------
- import calculator
  Imports the complete module.

- from calculator import add
  Imports a specific function or object.

- import calculator as calc
  Imports a module with an alias.

- from calculator import add as addition
  Imports an object with an alias.

7. IMPORT ALIAS
---------------
- The 'as' keyword provides an alternate name.
- Example:
  from app.api.upload import router as upload_router
- Original name = router.
- Alias = upload_router.

8. MODULE SEARCH PATH
---------------------
- Python uses sys.path to locate modules.
- It contains script-related locations, configured paths,
  standard library and installed package locations.
- sys.path can be inspected using:

  import sys
  print(sys.path)

9. IMPORT EXECUTION
-------------------
- Python locates the module.
- Loads and executes its top-level code.
- Creates or loads the module object.
- Stores loaded modules in sys.modules.
- Makes the imported object available.

10. APPLICATION TO EXAM INTELLIGENCE
------------------------------------
- app is the main package.
- api, auth and db organize related functionality.
- upload.py handles upload-related routes.
- chat.py handles chat-related routes.
- routes.py handles authentication routes.
- models.py contains database model definitions.
- main.py imports and connects these components.

=========================================================
END OF TOPIC SUMMARY
=========================================================
"""


"""
LOGGING SUMMARY
---------------
Logging helps monitor application activities, track errors, and debug issues.

Log Levels:
- DEBUG: Detailed information for debugging.
- INFO: Normal application events and progress.
- WARNING: Potential issues that don't stop execution.
- ERROR: Failures during specific operations.
- CRITICAL: Serious failures affecting the application.

Common Uses:
- Track application startup and shutdown.
- Monitor API requests and responses.
- Track model loading and AI operations.
- Monitor document upload and processing.
- Debug RAG retrieval and Gemini responses.
- Identify errors and performance issues.

Log Output:
- StreamHandler: Displays logs in the terminal.
- FileHandler: Saves logs in a file (e.g., app.log).

Benefits:
- Makes application behavior easier to understand.
- Helps identify where and why errors occur.
- Makes debugging and maintenance easier.
- Provides visibility into backend operations.

Note:
Logging does not fix errors; it helps identify,
understand, and troubleshoot them.
"""
