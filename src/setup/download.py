from pathlib import Path

import kagglehub

output_dir = Path(__file__).parent.parent / "data"
path = kagglehub.dataset_download("rounakbanik/the-movies-dataset", output_dir=str(output_dir))

print("Path to dataset files:", path)
