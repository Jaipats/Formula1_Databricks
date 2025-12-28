# Databricks Notebook Setup Guide

## ⚠️ CRITICAL: Import Order in Databricks Notebooks

When using Databricks notebooks with custom modules and external packages, **import order is critical**!

## ✅ Correct Order

```python
# STEP 1: Install packages
# MAGIC %pip install pyyaml requests pandas

# STEP 2: Restart Python (this loads the installed packages)
dbutils.library.restartPython()

# STEP 3: Do imports AFTER restart
import sys
sys.path.append('/Workspace/Users/your.email@domain.com/Formula1_Databricks')

from config.settings import config  # Now yaml is available!
from utils.api_client import OpenF1Client
# ... other imports

# STEP 4: Use the imported modules
print(f"Catalog: {config.catalog}")  # ✓ Works!
```

## ❌ Wrong Order (Will Fail!)

```python
# STEP 1: Install packages
# MAGIC %pip install pyyaml requests pandas

# STEP 2: Import modules ← WRONG! pyyaml not loaded yet!
from config.settings import config  # ERROR: ModuleNotFoundError: No module named 'yaml'

# STEP 3: Restart Python ← This wipes out all imports!
dbutils.library.restartPython()

# STEP 4: Try to use config
print(f"Catalog: {config.catalog}")  # ERROR: NameError: name 'config' is not defined
```

## 🔍 Why This Happens

1. **`%pip install`** installs packages but doesn't load them into the current Python session
2. **`restartPython()`** restarts the Python interpreter, which:
   - ✅ Makes newly installed packages available for import
   - ❌ **Clears ALL variables and imports** from before the restart
3. **Imports must happen AFTER restart** to access the newly installed packages

## 📝 Common Errors and Solutions

### Error 1: `ModuleNotFoundError: No module named 'yaml'`

**Cause**: Trying to import `config.settings` before `restartPython()` loads `pyyaml`

**Solution**: Move all imports to AFTER `restartPython()`

### Error 2: `NameError: name 'config' is not defined`

**Cause**: Imported `config` before `restartPython()`, which cleared it

**Solution**: Move all imports to AFTER `restartPython()`

### Error 3: `ModuleNotFoundError: No module named 'utils'`

**Cause**: `sys.path.append()` happened before `restartPython()`

**Solution**: Do `sys.path.append()` AFTER `restartPython()`

## 🎯 Best Practice Template

Use this template for all Databricks notebooks that need custom packages:

```python
# Databricks notebook source

# Cell 1: Install packages
# MAGIC %pip install package1 package2 package3

# Cell 2: Restart Python (separate cell!)
dbutils.library.restartPython()

# Cell 3: Setup imports (separate cell!)
import sys
import os

# Add your project to path
sys.path.append('/Workspace/Users/YOUR_EMAIL/YOUR_PROJECT')

# Import standard libraries
import logging
from datetime import datetime

# Import your custom modules
from config.settings import config
from utils.your_module import YourClass

# Setup logging, etc.
logging.basicConfig(level=logging.INFO)

# Cell 4+: Use your imports
print(f"Config loaded: {config.catalog}")
```

## 📌 Key Rules

1. ✅ **Install** → **Restart** → **Import** → **Use**
2. ✅ Put `restartPython()` in its own cell
3. ✅ Do ALL imports after `restartPython()`
4. ✅ Do `sys.path.append()` before importing custom modules
5. ❌ Never import before `restartPython()`
6. ❌ Never try to use variables from before `restartPython()`

## 🚀 Notebooks in This Project

Both notebooks follow this pattern:

- ✅ `notebooks/01_ingest_f1_data.py` - Follows correct order
- ✅ `notebooks/01_ingest_f1_data_incremental.py` - Follows correct order

## 🔧 Troubleshooting

If you get import errors:

1. Check the cell order in your notebook
2. Ensure `restartPython()` is in its own cell
3. Ensure ALL imports are in cells AFTER `restartPython()`
4. Check that `sys.path.append()` points to your actual workspace path
5. Update the path to match your Databricks username:
   ```python
   sys.path.append('/Workspace/Users/YOUR_EMAIL@databricks.com/Formula1_Databricks')
   ```

## 📖 References

- [Databricks: Python Libraries](https://docs.databricks.com/libraries/index.html)
- [Databricks: %pip magic command](https://docs.databricks.com/libraries/notebooks-python-libraries.html#install-a-library-with-pip)
- [Databricks: dbutils.library.restartPython()](https://docs.databricks.com/dev-tools/databricks-utils.html#restart-python-process)

