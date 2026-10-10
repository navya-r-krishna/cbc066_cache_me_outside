"""Run:  python demo.py --mock     (no API key needed)
       GEMINI_API_KEY=... python demo.py   (real Gemini)"""
import os
import sys

# Ensure backend_b is in sys.path
backend_b_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend_b")
if backend_b_dir not in sys.path:
    sys.path.insert(0, backend_b_dir)

if __name__ == "__main__":
    import runpy
    demo_script = os.path.join(backend_b_dir, "demo.py")
    runpy.run_path(demo_script, run_name="__main__")
