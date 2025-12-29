# 🚨 How to Disable Auto-Format in Cursor IDE

## The Problem

**Your Cursor IDE keeps auto-formatting the notebooks and moving imports BEFORE `restartPython()`**, which breaks them every time you save!

This causes:
- ❌ "Fatal error: The Python kernel is unresponsive"
- ❌ `NameError: name 'config' is not defined`
- ❌ Notebook crashes

---

## ✅ Solution: Disable Auto-Format for Notebook Files

### Option 1: Disable for Specific Files (Recommended)

Add this to your `.vscode/settings.json` or Cursor settings:

```json
{
  "files.associations": {
    "notebooks/*.py": "python"
  },
  "[python]": {
    "editor.formatOnSave": false,
    "editor.formatOnType": false,
    "editor.formatOnPaste": false
  }
}
```

### Option 2: Disable Auto-Format Globally

In Cursor/VS Code:

1. Open **Settings** (Cmd+, on Mac, Ctrl+, on Windows)
2. Search for **"format on save"**
3. **Uncheck** "Editor: Format On Save"
4. Search for **"format on type"**
5. **Uncheck** "Editor: Format On Type"
6. Search for **"format on paste"**
7. **Uncheck** "Editor: Format On Paste"

### Option 3: Use Keyboard Shortcut

Instead of auto-format, manually format when needed:
- **Mac**: Shift+Option+F
- **Windows/Linux**: Shift+Alt+F

**But DON'T use this on notebook files!**

---

## 🎯 Why This Matters

Databricks notebooks have a special requirement:

```python
# Cell 1: Install packages
%pip install pyyaml requests pandas

# Cell 2: Restart Python (ALONE!)
dbutils.library.restartPython()

# Cell 3: Import modules (AFTER restart)
import sys
from config.settings import config
```

**`restartPython()` terminates the Python kernel**. Any imports before it are lost, causing the kernel to become unresponsive.

Your IDE's auto-format follows PEP8, which says "imports should be at the top". But this breaks Databricks notebooks!

---

## 📋 Quick Check

After disabling auto-format, verify your notebooks look like this:

```python
# COMMAND ----------
%pip install pyyaml requests pandas

# COMMAND ----------
# ⚠️ NO IMPORTS HERE! ⚠️
dbutils.library.restartPython()

# COMMAND ----------
# ✅ Imports go here
import sys
from config.settings import config
```

If imports are before `restartPython()`, manually move them AFTER it.

---

## 🛠️ Alternative: Use .editorconfig

Create a `.editorconfig` file in your project root:

```ini
# EditorConfig for Formula1_Databricks project
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true

# Databricks notebooks - NO auto-format!
[notebooks/*.py]
trim_trailing_whitespace = false
indent_style = space
indent_size = 4
# Don't auto-format these files
max_line_length = off
```

---

## ✅ Verify It's Working

1. Open a notebook file (e.g., `01_ingest_f1_data_incremental_FIXED.py`)
2. Make a small change (add a space)
3. Save the file (Cmd+S / Ctrl+S)
4. Check if imports moved before `restartPython()`
   - ✅ If they stayed in place: Auto-format is disabled!
   - ❌ If they moved: Try another option above

---

## 📚 More Info

- `.cursorrules` file in the project root already tells Cursor not to format these files
- But you may need to manually disable it in settings too
- This is a Databricks-specific requirement and cannot be changed

---

## 🆘 If You Forget and Auto-Format Runs

1. **Don't panic!**
2. Press **Cmd+Z / Ctrl+Z** to undo
3. Save again
4. Or just pull the latest code from GitHub (it's already fixed there)

---

**Remember**: These notebooks ONLY run in Databricks, not locally. The import order is critical for them to work!

