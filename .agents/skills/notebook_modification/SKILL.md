---
name: notebook_modification
description: Safely updates specific cells (model, data pipeline, compression) in Jupyter Notebooks.
---

# Notebook Modification Skill

**Goal**: Update specific components (Model architecture, Data processing pipeline, Compression algorithms) of a Jupyter Notebook (`.ipynb`) without manually editing the JSON structure, which can cause corruption. This skill works across multiple notebook templates (e.g., `SisFall_KFold_Experiments_*.ipynb` and standard `train_v*.ipynb`).

## Rules
1. **Never edit `.ipynb` files directly via text replacement tools.**
2. When the user asks to modify a model, data pipeline, or compression algorithm in a notebook, you **MUST** use the provided python script `d:\datn\sis_fall_har_and_fall-detection_trainning\manage_notebook_cells.py`.

## Target Cell Identification
Determine which cell needs updating based on the user's request by picking a unique string found in that cell:

### For KFold Notebooks (e.g., `SisFall_KFold_Experiments_v3.ipynb`)
- **Model Definition**: Use `--search-string "def build_model"`
- **Data Pipeline**: Use `--search-string "class KFoldDataManager"`

### For Standard Training Notebooks (e.g., `train_v30.ipynb`)
- **Model Definition**: Use `--search-string "from tensorflow.keras.models import Model"` (This cell usually contains the CNN/TCN build functions).
- **Data Pipeline / Preprocessing**: Use `--search-string "class DataPreprocessor:"` or `--search-string "class FallDetectionTrainer"` depending on where the logic lives.
- **TFLite Compression/Export**: Use `--search-string "Export INT8 TFLite"`

## Workflow Execution Steps
When triggered:
1. **Understand the Change**: Analyze the user's requested changes for the model/pipeline.
2. **Write Temporary File**: Create a temporary Python file (`temp_update.py`) containing the *entire new code* for that specific cell.
   - Example: If changing the model, write the full imports + `def build_model(...)` function with the new architecture.
3. **Execute Replacement**: Run the modifier script:
   ```bash
   python d:\datn\sis_fall_har_and_fall-detection_trainning\manage_notebook_cells.py --notebook "path/to/notebook.ipynb" --search-string "<TARGET_SEARCH_STRING>" --code-file "temp_update.py"
   ```
4. **Cleanup**: Delete `temp_update.py` and notify the user that the notebook has been updated safely.
