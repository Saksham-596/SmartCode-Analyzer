from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import joblib
import ast
import os

app = FastAPI(title="Code Complexity Predictor API")


app.add_middleware(
    CORSMiddleware,
   allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

try:
    model = joblib.load('complexity_model.pkl')
except Exception as e:  
    print(f"Error loading model: {e}")
    model = None
class CodeRequest(BaseModel):
    code: str    
    language : str 
class ComplexityFeatureExtractor(ast.NodeVisitor):
    def __init__(self):
        self.num_loops = 0
        self.max_loop_depth = 0
        self.linear_loops = 0
        self.log_loops = 0
        self.constant_loops = 0
        self.recursive_calls = 0
        self.function_calls = 0
        self.list_comprehensions = 0
        
        self.n_log_n_calls = 0  
        self.log_n_calls = 0    

        self.current_depth = 0
        self.current_function = None

    def _enter_loop(self):
        self.num_loops += 1
        self.current_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_depth)

    def _exit_loop(self):
        self.current_depth -= 1

    def visit_For(self, node):
        self._enter_loop()
        
        is_constant = False
        if isinstance(node.iter, ast.Call) and getattr(node.iter.func, 'id', '') == 'range':
            if all(isinstance(arg, ast.Constant) and isinstance(arg.value, int) for arg in node.iter.args):
                is_constant = True
                
        if is_constant:
            self.constant_loops += 1
        else:
            self.linear_loops += 1

        self.generic_visit(node)
        self._exit_loop()

    def visit_While(self, node):
        self._enter_loop()
        self.linear_loops += 1 
        self.generic_visit(node)
        self._exit_loop()

    def visit_ListComp(self, node):
        self.list_comprehensions += 1
        self._enter_loop()
        self.linear_loops += 1  
        self.generic_visit(node)
        self._exit_loop()
        
    def visit_DictComp(self, node):
        self.list_comprehensions += 1
        self._enter_loop()
        self.linear_loops += 1
        self.generic_visit(node)
        self._exit_loop()

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        self.function_calls += 1
        
        if isinstance(node.func, ast.Name):
            if node.func.id == self.current_function:
                self.recursive_calls += 1
            elif node.func.id == 'sorted':
                self.n_log_n_calls += 1
            elif node.func.id in ['bisect', 'bisect_left', 'bisect_right']:
                self.log_n_calls += 1

        elif isinstance(node.func, ast.Attribute):
            if node.func.attr == 'sort':
                self.n_log_n_calls += 1
            elif node.func.attr in ['heappush', 'heappop', 'heapify', 'bisect', 'bisect_left', 'bisect_right']:
                self.log_n_calls += 1
                
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.op, (ast.FloorDiv, ast.Div, ast.RShift)):
            if isinstance(node.value, ast.Constant) and node.value.value == 2:
                self.log_loops += 1
        elif isinstance(node.op, (ast.Mult, ast.LShift)):
            if isinstance(node.value, ast.Constant) and node.value.value == 2:
                self.log_loops += 1
                
        self.generic_visit(node)
import requests

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"

@app.post("/predict")
async def predict_complexity(request: CodeRequest):
    prediction = "--"
    
    # ast logging for python
    if "python" in request.language.lower():
        try:
            tree = ast.parse(request.code)
            extractor = ComplexityFeatureExtractor()
            extractor.visit(tree)
            print(f"INTERNAL AST LOG: Max Loop Depth: {extractor.max_loop_depth}")
        except Exception as e:
            print(f"AST Parsing skipped: {e}")

    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    f"You are a Senior Algorithm Engineer. Analyze the exact time complexity of the following {request.language} code. "
                    "only give the final complexity in big O notation , no explanations. If you are unsure, give your best guess. "
                    f"Code:\n{request.code}"
                )
            }]
        }]
    }
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prediction = data['candidates'][0]['content']['parts'][0]['text'].strip().split('\n')[0].replace(".", "")
        
    except Exception as e:
        print(f"API Error: {e}")
        prediction = "O(N)"
    return {"complexity": prediction}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)