import ast
import csv
import requests
import json

# ==========================================
# 1. The Label Map (Data Cleaning)
# ==========================================
LABEL_MAP = {
    "constant": "O(1)",
    "logn": "O(log N)",
    "linear": "O(N)",
    "nlogn": "O(N log N)",
    "quadratic": "O(N^2)",
    "cubic": "O(N^3)",
    "np": "O(2^N)" 
}

# ==========================================
# 2. The Final Custom AST Feature Extractor
# ==========================================
class ComplexityFeatureExtractor(ast.NodeVisitor):
    def __init__(self):
        # Your 8 Core Features
        self.num_loops = 0
        self.max_loop_depth = 0
        self.linear_loops = 0
        self.log_loops = 0
        self.constant_loops = 0
        self.recursive_calls = 0
        self.function_calls = 0
        self.list_comprehensions = 0
        
        # The 2 Standard Library Features
        self.n_log_n_calls = 0  
        self.log_n_calls = 0    

        # State trackers
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
        
        # Check if it's a constant loop like 'for i in range(100)'
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
        
        # 1. Catch standalone functions: sorted(), bisect(), recursion
        if isinstance(node.func, ast.Name):
            if node.func.id == self.current_function:
                self.recursive_calls += 1
            elif node.func.id == 'sorted':
                self.n_log_n_calls += 1
            elif node.func.id in ['bisect', 'bisect_left', 'bisect_right']:
                self.log_n_calls += 1

        # 2. Catch object methods: arr.sort(), heapq.heappush()
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr == 'sort':
                self.n_log_n_calls += 1
            elif node.func.attr in ['heappush', 'heappop', 'heapify', 'bisect', 'bisect_left', 'bisect_right']:
                self.log_n_calls += 1
                
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        # Track log_loops by catching halving (n //= 2) or doubling (n *= 2)
        if isinstance(node.op, (ast.FloorDiv, ast.Div, ast.RShift)):
            if isinstance(node.value, ast.Constant) and node.value.value == 2:
                self.log_loops += 1
        elif isinstance(node.op, (ast.Mult, ast.LShift)):
            if isinstance(node.value, ast.Constant) and node.value.value == 2:
                self.log_loops += 1
                
        self.generic_visit(node)

# ==========================================
# 3. The Dataset Generator
# ==========================================
def generate_real_world_dataset():
    print("Downloading the 2024 Python CodeComplex dataset from GitHub...")
    url = "https://raw.githubusercontent.com/sybaik1/CodeComplex-Data/main/python_data.jsonl"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Failed to download data. Check your internet connection.")
        return

    lines = response.text.strip().split('\n')
    rows = []
    success_count = 0
    fail_count = 0
    
    print(f"Downloaded {len(lines)} real-world Python submissions.")
    print("Extracting features (Loops, Comprehensions, HeapQ, Sorts, etc.)...")
    
    for line in lines:
        try:
            data = json.loads(line)
            raw_code = data['src']
            raw_label = data['complexity'].lower()
            expert_label = LABEL_MAP.get(raw_label, raw_label)
            
            tree = ast.parse(raw_code)
            extractor = ComplexityFeatureExtractor()
            extractor.visit(tree)
            
            row = [
                extractor.num_loops,
                extractor.max_loop_depth,
                extractor.linear_loops,
                extractor.log_loops,
                extractor.constant_loops,
                extractor.recursive_calls,
                extractor.function_calls,
                extractor.list_comprehensions,
                extractor.n_log_n_calls,
                extractor.log_n_calls,
                expert_label
            ]
            rows.append(row)
            success_count += 1
        except Exception:
            fail_count += 1
    with open("real_world_ast_dataset.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "num_loops", "max_loop_depth", "linear_loops", "log_loops", 
            "constant_loops", "recursive_calls", "function_calls", "list_comprehensions",
            "n_log_n_calls", "log_n_calls", "Complexity"
        ])
        writer.writerows(rows)
        
    print(f"\nSuccess! Extracted {success_count} valid Python submissions.")
    print("Saved to real_world_ast_dataset.csv")

if __name__ == "__main__":
    generate_real_world_dataset()