# ai-Data-Center-Visualization
Interactive dashboard visualizing the [Epoch AI Frontier Data Centers](https://epoch.ai/data/data-centers) dataset — 50 frontier AI compute facilities worldwide, with a geographic map, compute growth timeline, and owner comparison.

## Running the project

**1. Generate the dashboard** (required after any CSV update):
```bash
python3 generate.py
```
This reads the CSVs in `data/` and writes `index.html`.

**2. Serve locally:**
```bash
python3 -m http.server 8000
```
Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Data

Source CSVs live in `data/` and come from [Epoch AI](https://epoch.ai/data/data-centers) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

| File | Contents |
|---|---|
| `data_centers.csv` | One row per facility — compute, power, cost, owner, location |
| `data_center_timelines.csv` | Construction milestones and capacity over time |
| `data_center_chillers.csv` | Chiller hardware specs |
| `data_center_cooling_towers.csv` | Cooling tower hardware specs |
