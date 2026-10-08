#!/bin/zsh
set -e

PROJECT="$HOME/Downloads/contract_field_extractor"

echo "Project: $PROJECT"
mkdir -p "$PROJECT"

# After extracting/copying this project, place your data here:
mkdir -p "$PROJECT/dataset/training_docs"
mkdir -p "$PROJECT/dataset/evaluation_docs"

echo ""
echo "Next:"
echo "1. Copy train.csv -> $PROJECT/dataset/train.csv"
echo "2. Copy test.csv  -> $PROJECT/dataset/test.csv"
echo "3. Copy training documents -> $PROJECT/dataset/training_docs/"
echo "4. Copy test documents -> $PROJECT/dataset/evaluation_docs/"
echo "5. cd $PROJECT"
echo "6. python3.12 -m venv .venv"
echo "7. source .venv/bin/activate"
echo "8. pip install -r requirements.txt"
echo "9. python inspect_dataset.py"
echo "10. python train_pipeline.py"
echo "11. python predict_documents.py"
echo "12. python evaluation/evaluate_predictions.py"
