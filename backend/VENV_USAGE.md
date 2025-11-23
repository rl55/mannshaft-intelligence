# Using Virtual Environment for Backend Scripts

## Setup

The backend has a virtual environment at `backend/venv/`. When running Python scripts, always activate it first:

```bash
cd backend
source venv/bin/activate
python your_script.py
```

## Helper Script

A helper script `run_test.sh` is provided for running tests:

```bash
cd backend
./run_test.sh
```

## Note

If dependencies are not installed in the venv, install them first:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## For AI Assistant

When executing Python scripts in the backend, use:

```bash
cd backend && source venv/bin/activate && python script.py
```

Or use the venv Python directly:

```bash
cd backend && venv/bin/python script.py
```

