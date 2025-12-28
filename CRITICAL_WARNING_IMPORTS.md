# ⚠️ CRITICAL WARNING: Import Order in Databricks Notebooks ⚠️

## 🚨 DO NOT IGNORE THIS

If you're getting:
- `NameError: name 'config' is not defined`
- `Fatal error: The Python kernel is unresponsive`
- Notebook hangs or crashes

**YOU HAVE IMPORTS BEFORE `restartPython()`** ← This is the problem!

---

## ❌ WRONG (Causes Kernel Unresponsiveness)

```python
# Cell 1: Install packages
%pip install pyyaml requests pandas

# Cell 2: THIS IS WRONG! ❌
from config.settings import config  # ← WRONG! Importing first
from utils.api_client import OpenF1Client  # ← WRONG!
import sys  # ← WRONG!
dbutils.library.restartPython()  # ← This KILLS the kernel!

# Cell 3: Try to use imports
print(config.catalog)  # ← Kernel is unresponsive or NameError!
```

### What Happens:
1. ❌ You import `config`, `sys`, etc.
2. ❌ You call `restartPython()` which **TERMINATES the Python kernel**
3. ❌ The kernel restarts but your imports are GONE
4. ❌ Code tries to run but kernel is in a broken state
5. ❌ Result: "Fatal error: The Python kernel is unresponsive"

---

## ✅ CORRECT (Works Every Time)

```python
# Cell 1: Install packages
%pip install pyyaml requests pandas

# Cell 2: Restart ONLY (no imports!)
# ⚠️ WARNING: DO NOT ADD IMPORTS BEFORE THIS LINE! ⚠️
dbutils.library.restartPython()

# Cell 3: NOW import (after restart) ✅
import sys
import os
from config.settings import config
from utils.api_client import OpenF1Client

# Cell 4: Use the imports ✅
print(config.catalog)  # ← Works perfectly!
```

### What Happens:
1. ✅ You install packages with `%pip`
2. ✅ You restart Python (loads packages, clears everything)
3. ✅ You import modules (pyyaml is now available)
4. ✅ You use the imports (everything works!)

---

## 🎯 The Rule (Read This 3 Times)

### **`restartPython()` MUST be in its own cell with NOTHING before it except comments**

```python
# ✅ CORRECT:
# Cell 1: %pip install pyyaml
# Cell 2: dbutils.library.restartPython()  ← ALONE!
# Cell 3: import config, etc.

# ❌ WRONG:
# Cell 1: %pip install pyyaml  
# Cell 2: import config       ← WRONG!
#         restartPython()      ← WRONG!
# Cell 3: use config           ← Kernel unresponsive!
```

---

## 🔍 Why This Keeps Happening

Many IDEs (like Cursor) auto-format code and may move imports to the top. **This breaks Databricks notebooks!**

### If Your IDE Moves Imports:

1. **Don't let it!** Manually move them back after restart
2. **Use the FIXED notebook** which has clear warnings
3. **Add a comment** so your IDE doesn't auto-format:

```python
# COMMAND ----------
# DO NOT ADD IMPORTS HERE - restartPython() must be alone!
dbutils.library.restartPython()

# COMMAND ----------
# Imports go here (after restart)
import sys
from config.settings import config
```

---

## 🛠️ How to Fix Right Now

### Step 1: Check Your Notebook

Look at the cell with `restartPython()`. Does it look like this?

```python
# ❌ BAD (this is what you have):
from config.settings import config  # ← These imports are WRONG!
from utils.api_client import OpenF1Client
dbutils.library.restartPython()
```

### Step 2: Fix It

**Delete all imports before `restartPython()`:**

```python
# ✅ GOOD (after fix):
# ⚠️ WARNING: NO IMPORTS BEFORE THIS LINE!
dbutils.library.restartPython()
```

### Step 3: Move Imports to Next Cell

```python
# ✅ Cell AFTER restartPython():
import sys
import os
from config.settings import config
from utils.api_client import OpenF1Client
# ... rest of imports
```

### Step 4: Run Again

Now your notebook will work!

---

## 📋 Checklist Before Running

Before you run your notebook, verify:

- [ ] Cell 1: `%pip install pyyaml requests pandas`
- [ ] Cell 2: ONLY `dbutils.library.restartPython()` (no imports!)
- [ ] Cell 3: All imports (after restart)
- [ ] No imports before `restartPython()`
- [ ] Workspace path is correct

---

## 🎓 Understanding `restartPython()`

Think of `restartPython()` like **restarting your computer**:

```
Your Computer:
1. Open Microsoft Word
2. Type a document
3. Restart computer  ← This closes EVERYTHING!
4. Try to continue typing  ← ERROR! Word is closed!

Your Notebook:
1. Import modules
2. Set up variables
3. restartPython()  ← This clears EVERYTHING!
4. Try to use modules  ← ERROR! Imports are gone!
```

**Solution**: Import AFTER the restart, not before!

---

## 📁 Which Notebooks Are Fixed?

All three notebooks have been fixed with clear warnings:

1. ✅ `notebooks/01_ingest_f1_data.py` - Has warning comments
2. ✅ `notebooks/01_ingest_f1_data_incremental.py` - Has warning comments  
3. ✅ `notebooks/01_ingest_f1_data_incremental_FIXED.py` - Has warning comments + memory efficient

**RECOMMENDATION**: Use `01_ingest_f1_data_incremental_FIXED.py`
- ✅ Correct import order with clear warnings
- ✅ Memory-efficient (won't crash)
- ✅ Best for production use

---

## 🚨 Final Warning

**PLEASE DO NOT MOVE IMPORTS BEFORE `restartPython()` AGAIN!**

Every time you do this:
- ❌ The kernel becomes unresponsive
- ❌ You get NameError
- ❌ The notebook crashes
- ❌ You have to fix it again

The notebooks are now fixed with clear warnings. **Please leave the import order as-is!**

---

## 💡 Quick Reference

**Wrong Order** (Kernel Unresponsive):
```
Import → Restart → Broken Kernel ❌
```

**Correct Order** (Works):
```
Restart → Import → Everything Works ✅
```

---

## 📚 More Help

- `DATABRICKS_NOTEBOOK_SETUP.md` - Detailed explanation
- `NOTEBOOK_CRASH_FIX.md` - Crash troubleshooting
- `QUICK_START.md` - Getting started guide

---

## ✅ Summary

1. **Install packages** with `%pip`
2. **Restart Python** with `restartPython()` (ALONE IN ITS OWN CELL!)
3. **Import modules** in the NEXT cell
4. **Use the imports** - everything works!

**DO NOT** put imports before `restartPython()`! This causes kernel unresponsiveness. 🚫


