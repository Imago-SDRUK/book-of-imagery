---
editor_options: 
  markdown: 
    wrap: 72
---

# Google Satellite Embedding V1 - small areas (2017-2024)

## Abstract

This report describes the development, methodology, and validation of
the Imago Embedding data product, a UK-wide dataset of satellite-derived
embedding vectors aggregated to small-area statistical geographies
across the United Kingdom (UK), including Lower Layer Super Output Areas
(England and Wales), Data Zones (Scotland), and Super Output Areas
(Northern Ireland), for the years 2017–2024. The data product is derived
from the [AlphaEarth Foundations Satellite Embedding Dataset
V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL).
The workflow consists of two automated pipelines: a Google Earth Engine
export pipeline that retrieves and tiles 64-dimensional Embeddings
across British National Grid tiles, and aggregation pipeline that
computes mean embedding vectors for each of the small statistical areas
in the UK. The resulting GeoPackage output provides 64-dimensional
embedding vectors (range [−1, 1]) for each small area statistical
geography and year. Validation confirms 100% range compliance across
\~24 million values and near-perfect correlation (mean r = 0.997)
without systematic bias. The data product is published via the [Imago
Data
Catalogue](https://data.imago.ac.uk/datasets/google-satellite-embedding-v1-small-areas-2017-2024)
and is intended to support small-area analysis, spatial planning, urban
research, and policy applications.

## Keywords

Satellite embeddings; Earth observation; Small area statistical
geography; Health and Wellbeing; Sustainability; Google embeddings;
LSOA; UK

------------------------------------------------------------------------

## 1. Introduction

### 1.1 Background

Satellite-derived embeddings represent a new approach in geospatial
science that summarises complex patterns contained within Earth
observation imagery into compact numerical representations. These
representations capture information about the physical and environmental
characteristics of places while substantially reducing data complexity.
The [AlphaEarth Foundations Satellite Embedding Dataset
V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL),
produced by Google **DeepMind** and available on Google Earth Engine,
provides 64-dimensional, L2-normalised embedding vectors at 10-metre
spatial resolution derived from annual satellite composites for
2017-2024. These embeddings capture rich environmental and structural
information latent in satellite imagery, providing a foundation for a
wide range of downstream analytical tasks, including classification,
clustering, similarlity analysis, environmental characterisation, and
predictive modelling.

Rather than representing specific land-cover classes, the embedding
dimensions encode complex combinations of spectral, environmental, and
built-environment characteristics learned from large volumes of
satellite imagery. Areas with similar environmental and physical
characteristics therefore tend to exhibit similar embedding
representations, even when individual dimensions may not have direct
physical interpretations. However, direct use of pixel-level embedding
data at national scale is computationally demanding for most research
and policy applications. This data product aims to aggregate these
embeddings to small-area statistical geographies across the United
Kingdom, including Lower Layer Super Output Areas (England and Wales),
Data Zones (Scotland), and Super Output Areas (Northern Ireland), making
them more usable for social science, urban analysis, and policy
research.

### 1.2 Motivation

Small-area statistical geographies form the foundation of a large
proportion of UK government statistics and policy analysis. They are
widely used in the Census, the Index of Multiple Deprivation, public
health monitoring, housing analysis, transport planning, and
environmental assessment. Aggregating satellite-derived embeddings to
these established geographies creates opportunities to integrate Earth
observation-derived information with existing socioeconomic,
demographic, and environmental datasets. Although there is a clear
potential of satellite embeddings for characterising local environments,
there is currently no publicly available data product which aggregates
AlphaEarth satellite embeddings to UK small-area statistical geographies
across the full 2017–2024 temporal range.

Because AlphaEarth embeddings are continuous latent representations
normalised to a common feature space, arithmetic averaging provides a
practical method for summarising neighbourhood-scale characteristics
while preserving broad similarity relationships between areas. This
enables embeddings to be analysed using conventional statistical and
machine learning approaches while substantially reducing computational
requirements compared with pixel-level datasets, thereby making the
information more accessible for research, planning, and policy
applications.

### 1.3 Objectives

This data product and the accompanying technical report have the
following objectives:

-   To develop a reproducible, automated pipeline for extracting and
    processing annual satellite embedding data from Google Earth Engine
    **(GEE)** at UK national scale.
-   To aggregate pixel-level embedding vectors to UK small-area
    statistical geographies using a tile-aware weighted averaging
    procedure.
-   To validate the resulting data product against direct Earth Engine
    extraction and confirm compliance with the theoretical embedding
    data value range.
-   To publish the validated dataset via the Imago Data Catalogue in an
    accessible, well-documented format for use by researchers and policy
    professionals.

### 1.4 Contributions

The principal contributions of this work are:

-   A UK-wide annual embedding dataset providing 64-dimensional
    satellite-derived embedding vectors for small-area statistical
    geographies across England, Wales, Scotland, and Northern Ireland
    between 2017 and 2024.
-   A reproducible aggregation framework implementing pixel-weighted,
    multi-tile averaging for transforming pixel-level embedding data
    into neighbourhood-scale representations.
-   A quantitative validation framework comparing pipeline outputs
    against direct Earth Engine extraction.
-   A command-line tool for batch export of annual Google Earth Engine
    image collections to tiled GeoTIFF format.
-   A scalable processing workflow that can be adapted to alternative
    administrative, statistical, or custom geographies.

For further details on the original Embedding dataset, see [this
blogpost](https://medium.com/google-earth/ai-powered-pixels-introducing-googles-satellite-embedding-dataset-31744c1f4650).

## 2. Source Data and Study Area

### 2.1 Original Google Satellite Embedding Dataset

The source data for this product is the [AlphaEarth Foundations
Satellite Embedding Dataset
V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL),
available on Google Earth Engine. This dataset provides annual 64-band
raster dataset representing L2-normalised embedding vectors at 10-metre
spatial resolution, with values bounded within [−1, 1]. The collection
spans 2017 to 2024. An alternative distribution of the same underlying
embeddings is available via [Source
Cooperative](https://source.coop/tge-labs/aef). In that product,
AlphaEarth Foundation Embeddings are stored in signed 8-bit data type
through nonlinear scaling, with `−128` as the nodata value and the
spatial index recorded within the filenames. This substantially reduces
storage requirements but introduces a loss of numerical precision
compared with the original Google Earth Engine distribution (see Section
3.4 and Appendix E).

All processing undertaken for this data product utilised the AlphaEarth
Foundations dataset from Google Earth Engine, which represented the most
recent version available at the time of processing.

### 2.2 Geographic Coverage and Aggregation Units

The target geographic unit for aggregation is the set of official
small-area statistical geographies used across the UK, comprising Lower
Layer Super Output Area (LSOA), the standard small-area statistical
geography for England and Wales, Data Zones in Scotland, and Super
Output Areas in Northern Ireland. The resulting dataset covers 46,844
small-area statistical geographies annually between 2017 and 2024 and is
from the [Imago Data
Catalogue](https://data.imago.ac.uk/datasets/lsoa-boundaries-for-the-united-kingdom-2021).

### 2.3 Input Data Specifications

The input data as received from Google Earth Engine has the following
characteristics:

-   **Format:** GeoTIFF, optionally with COG (Cloud-Optimised GeoTIFF)
    layout.
-   **Bands:** 64 bands, labelled A00 to A63.
-   **Data type:** Int16, LZW compression.
-   **CRS:** UTM zone projection
-   **Spatial resolution:** 10 m
-   **NoData:** The exported embedding tiles contain valid embedding
    values throughout the image extent and do not define a separate
    NoData value.
-   **Tile edge artefact:** Exported tiles may contain one additional
    pixel along the northern and eastern edges due to pixel alignment
    and boundary handling during export (e.g., expected 2000 × 2000
    pixels yields 2001 × 2001 pixels in output).

## 3. Methodology

### 3.1 Workflow Overview

The IMAGO processing pipeline consists of three sequential processing
stages (*Figure 1*):

1.  **Data Extraction** – annual AlphaEarth embedding data are retrieved
    from Google Earth Engine and exported as GeoTIFF imagery covering
    the area of interest.

2.  **Data Preparation** – exported imagery is reprojected to the
    British National Grid, organised into a standardised tiling
    structure, and transformed from floating-point values to a scaled
    Int16 representation to improve storage efficiency.

3.  **Small-Area Aggregation** – embedding values are aggregated from
    pixel level to small-area statistical geographies using zonal
    statistics and a tile-aware weighted averaging procedure.

The final output is a GeoPackage containing annual embedding vectors for
all small-area statistical geographies across the United Kingdom. These
stages are described in Sections 3.2–3.4.

![process_flowchart](images/methodology_flowchart.png)*Figure 1:
Conceptual flowchart illustrating the main processing steps*

### 3.2 Data Extraction

A command-line tool has been developed to access annual satellite
collections on Google Earth Engine, filter by the area and timeframe of
interest, and export in GeoTIFF format to Google Cloud Storage. This
tool can also be used to export tiles to Google Drive.

Main requirements are:

-   Polygonal area of interest, which can be tiled (for example, the UK
    gridded by tiles of 20 × 20 km)
-   Year of interest

The pipeline accesses the AlphaEarth embedding collection on Google
Earth Engine, filters the data according to the specified area and year
of interest, and exports the resulting imagery in batches through the
Google Earth Engine API (*Figure 2*).

![download_ee_flowchart](images/download_ee_flowchart.png) *Figure 2:
Conceptual flowchart illustrating the input data, input/output
operations, processing steps and output data in the Google Earth Engine
download pipeline*

In this pipeline, [batch export
tasks](https://developers.google.com/earth-engine/apidocs/export-image-tocloudstorage)
are used — `Export.image.toDrive` or `Export.image.toCloudStorage` —
which produce identical outputs.

Full CLI usage is documented in Appendix A.

### 3.3 Data Preparation

#### 3.3.1 Tiling Strategy

The Imago intermediate dataset in GeoTIFF format is gridded using 20 ×
20 km British National Grid (BNG) tiles, resulting in 858 tiles for the
full UK coverage. This tiling structure aligns with the OSGB36/British
National Grid (EPSG:27700) coordinate reference system used throughout
the intermediate processing stage. In contrast, the original AlphaEarth
embedding data covering the UK are distributed across 39 larger tiles
within GEE. During the data preparation stage, these tiles are
reprojected and regridded into the standaised BNG tile structure used
throughout the remainder of the workflow.

#### 3.3.2 Embedding Transformation and Scaling

To reduce storage requirements while preserving precision, the pipeline
optionally scales the native `float64` embedding values (range [−1, +1])
to `Int16` representation (range [−32767, +32767]), reducing output size
by approximately one third.

To recover original decimal values (to "descale"), apply:

$$x_\text{original} = \frac{x_\text{int16}}{32767}$$

The scaled Int16 representation preserves the original embedding values
with very high precision (Figure 3). Validation using tile SJ26 (2024)
indicates that scaling errors are centred around zero and exhibit no
evidence of systematic bias. The mean error and RMSE occur at
approximately the sixth decimal place, while the maximum absolute error
is approximately $1.6 \times 10^{-5}$, corresponding to the fifth
decimal place. These results demonstrate that the Int16 representation
provides substantial storage savings while maintaining effectively
lossless precision for downstream analysis. Full scaling precision
statistics are provided in Appendix E.

<img src="images/SJ26-2024_band1_difference_hist.png" width="60%"/>

Figure 3: Distribution of scaling errors between the original
floating-point embedding values and the corresponding Int16-scaled
representation for embedding dimension A00, Tile SJ26 (2024).

#### 3.3.3 Intermediate Data Specifications

After reprojection and scaling, the intermediate data has the following
characteristics:

-   **Format:** GeoTIFF (without COG layout).
-   **Bands:** 64 bands, labelled A00 to A63.
-   **Data type:** Int16, LZW compression.
-   **CRS:** EPSG:27700, OSGB36/British National Grid; spatial
    resolution 10 m.
-   **NoData:** Undefined, with one extra pixel along the northern and
    eastern tile edges. Pixels equal to 0 are filtered out during
    further processing to avoid calculation distortions.
-   **Tiling:** Gridded by 20 × 20 km National Grid tiles.
-   **Value range:** −32767 to +32767 (scaled); equivalent to [−1, +1]
    in original float64 space.

### 3.4 Small Area Aggregation

#### 3.4.1 LSOA Aggregation Pipeline

The aggregation pipeline converts tile-based embedding datasets into
small-area statistical geography summaries. For each year, the workflow
identifies all tiles intersecting a geographic unit, extracts the
corresponding embedding values, and computes mean values for each of the
64 embedding dimensions using zonal statistics. The output is a
GeoPackage containing one record per geographic unit and 64
corresponding embedding attributes. To facilitate processing of multiple
years, the workflow uses a set of configuration templates and automation
scripts (Figure 4). A master script, `run_all_years.sh`, generates a
year-specific configuration file (`config_$YEAR.yaml`) and execution
script (`run_$YEAR.sh`) for each year of interest (2017–2024). The
configuration file stores all processing parameters, including input and
output locations, memory allocation, and parallel processing settings,
while the execution script launches the aggregation workflow using these
settings.

*![](images/lsoa_extraction_flowchart.png) Figure 4: Conceptual
flowchart illustrating the input data, input/output operations,
processing steps and output data in the LSOA aggregation pipeline*

The aggregation itself is performed by `embed_to_lsoa.py`, which
accesses routines from the IMAGO toolkit repository. The workflow first
establishes the relationship between geographic units and the tiles that
intersect them, creating a tile-to-polygon mapping that identifies the
relevant embedding tiles for each LSOA. The required tiles are then
loaded and processed using zonal statistics to calculate mean embedding
values for each of the 64 embedding dimensions across all pixels falling
within the geographic unit boundary. To support national-scale
processing, calculations are parallelised using Dask, with geographic
units processed in chunks across multiple workers, while `rasterio`
performs the underlying raster operations and zonal statistics
calculations. This enables efficient processing of large embedding
datasets while maintaining a relatively modest computational footprint.

Because the workflow relies solely on a geographic boundary dataset as
input, the same aggregation procedure can readily be applied to
alternative geographies, including Middle Layer Super Output Areas
(MSOAs), local authority districts, Data Zones, Super Output Areas, or
custom administrative boundaries, provided that an appropriate
tile-to-polygon mapping can be established.

#### 3.4.2 Weighted Averaging Procedure for Multi-Tile Geographies

For LSOAs that span multiple tiles, a tile-aware weighted averaging
procedure is applied:

1.  The mean embedding value is calculated per tile for each LSOA-tile
    intersection.
2.  The number of overlapping pixels within each tile is recorded
    alongside the computed their computed mean.
3.  The final small area geography embedding vector is computed by
    averaging the per-tile mean embedding values using the number of
    overlapping pixels in each tile as weights.

For embedding dimension (j), the weighted average is calculated as:

$$
E_j=\frac{\sum_{i=1}^{n} p_iE_{ij}}{\sum_{i=1}^{n} p_i}
$$

where $E_j$ denotes the final LSOA-level embedding value for dimension
$j$, $E_{ij}$ denotes the mean embedding value for dimension $j$
calculated within tile $i$, $p_i$ denotes the number of overlapping
pixels within tile $i$, and $n$ denotes the number of intersecting
tiles.

This approach ensures that each tile contributes to the final embedding
vector in proportion to its spatial contribution to the geographic unit
being observed. This approach is necessary because some LSOAs,
particularly in areas near tile boundaries, may cover two or more 20 ×
20 km tiles. 

The current implementation uses `rasterio` for zonal statistics, which
benefits from a parallelised implementation that offered practical
performance advantages at the time of writing. `rasterio` treats all
overlapping pixels as contributing equally and does not apply fractional
weighting to partially intersected boundary pixels. While this may
introduce minor uncertainty along geographic boundaries, the effect is
expected to be limited given the 10-metre spatial resolution of the
source data. The implications of this assumption are examined in the
validation analysis presented in Section 5.

### 3.5 Computational Infrastructure and Parallel Processing

**3.5.1 GEE Export Pipeline**

Processing is performed on Google Earth Engine infrastructure. Two
distinct time concepts are relevant:

1.  **Python pipeline runtime** (client wall-clock time) — time on the
    client machine between two Python timestamps. Does not reflect
    billing or quota consumption.
2.  **EECU (Earth Engine Compute Units)** — compute consumption across
    all parallel workers; reflects billing and quotas. Includes I/O
    reads and array manipulations, but excludes latency, queue
    scheduling, client waiting, and Google Drive/Cloud upload time.

Python pipeline runtime is the sum of individual task runtimes plus
client-side preparation, initialisation, and scheduling time. Even
identical requests can be processed in very different times (see [GEE
Computation
Overview](https://developers.google.com/earth-engine/guides/computation_overview#stability_and_predictability)).
EECU time for the same area of interest has been observed to vary by a
factor of 2.8, while total runtime can vary by up to a factor of 8.8.
For detailed benchmarking tables, please see the Appendix B.

**3.5.2 LSOA Aggregation Pipeline**

The LSOA aggregation step is run on a virtual machine (VM) with 8 CPUs
and 32 GB of memory, chosen as a balance between performance and cost.
Data is accessed from Google Cloud Storage (GCS) via bucket mounting to
the VM, avoiding the need to download the complete dataset locally. This
introduces I/O overhead compared to local disk access, but avoids the
need to download the full dataset locally.

Key implementation choices for performance:

-   **Chunked band processing:** Calculation is split into groups of
    bands (e.g., 8 bands per chunk, 8 chunks for 64 bands total),
    enabling processing without spilling to disk.
-   **LRU caching:** `functools.lru_cache` is used to cache tile
    metadata from repeated `rasterio.open` calls, improving overall
    performance by approximately 25%.
-   **Dask parallelisation:** `dask` is used to parallelise over LSOAs
    in chunks, with 8 concurrent workers.

Using this configuration, the aggregation of a single annual dataset
requires approximately 1.5 hours on average. Consequently, the complete
2017–2024 time series can typically be processed within approximately
one day. Detailed benchmarking results and performance statistics are
provided in Appendix B.

## 4. Data Product Description

### 4.1 Output Structure

The output data product is distributed as eight annual GeoPackage
(.gpkg) files, one for each year between 2017 and 2024. Each file
contains one row per small-area statistical geography and the
corresponding embedding attributes. Each row contains the geometry of
the statistical geography (from [2021 LSOA
boundaries](https://data.imago.ac.uk/datasets/lsoa-boundaries-for-the-united-kingdom-2021))
and 64 embedding attributes. The product covers 46,844 small-area
statistical geographies annually across England, Wales, Scotland, and
Northern Ireland.

### 4.2 Embedding Dimensions

Each small-area statistical geography includes 64 embedding dimensions
(band1_mean to band64_mean), each representing the mean embedding value
across all pixels within the geographic unit for that dimension and
year. These are L2-normalised vectors derived from the AlphaEarth
Foundation model, encoding spectral and structural information from
annual satellite composites.

### 4.3 File Formats and Storage

The main output format is GeoPackage (`.gpkg`). During processing,
tiling, compression, and Int16 scaling were used to reduce storage
requirements for the intermediate embedding datasets. These procedures
reduced the total intermediate data volume from an estimated \~4 TiB
(unscaled floating-point values) to approximately 2.02 TiB (Int16,
LZW-compressed) across all eight years.

### 4.4 Metadata and Attribute Schema

The output GeoPackage includes:

-   A unique statistical geography identifier.

-   Polygon geometry representing the statistical geography boundary.

-   64 embedding attributes, each storing the mean embedding value for a
    single embedding dimension.

All embedding attributes are stored using double-precision
floating-point data types.

**Table 1 summarises the principal fields included in the GeoPackage.**

| Field Type | Description |
|---------------------|---------------------------------------------------|
| Geography ID | Unique identifier for the statistical geography |
| Geometry | Polygon boundary geometry |
| band1_mean – band64_mean | Mean embedding values for the 64 embedding dimensions |

Additional summary statistics, including median, minimum, maximum,
standard deviation, and sum, can be generated through the aggregation
pipeline if required. Full field descriptions are provided in Appendix
D.

## 5. Technical Validation

### 5.1 Validation Framework

Validation of the small-area statistical geography embedding datasets
was conducted through two primary checks:

1.  **Range validation** — verifying that all embedding values fall
    within the theoretical [−1, 1] bounds.
2.  **Random sampling validation** — comparing pipeline-generated mean
    embedding values against values extracted directly from Google Earth
    Engine for a random sample of geographic unit-year pairs.

Together, these validation procedures assess both compliance with the
theoretical properties of the AlphaEarth embeddings and the ability of
the aggregation workflow to reproduce values obtained directly from
Google Earth Engine (GEE).

| Validation Task | Description | Status |
|------------------------|------------------------|------------------------|
| Range Check | Verify all embedding values are within [−1, 1] | ✅ PASSED |
| Random Sampling Validation | Compare pipeline with EE extraction (100 samples) | ✅ PASSED |

### 5.2 Range Validation

The AlphaEarth embedding model produces values theoretically bounded
within [−1, 1]. This check systematically inspected every numeric value
across all 64 embedding dimensions for each year from 2017 to 2024.

-   Total values inspected per year: 46,844 geographic units × 64
    dimensions = 2,998,016 values
-   Total values inspected across 8 years: \~24 million values

| Year | LSOAs  | Dimensions | Total Values | Out-of-Range | Status |
|------|--------|------------|--------------|--------------|--------|
| 2017 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2018 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2019 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2020 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2021 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2022 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2023 | 46,844 | 64         | 2,998,016    | 0            | ✅     |
| 2024 | 46,844 | 64         | 2,998,016    | 0            | ✅     |

No out-of-range values were detected in any year or embedding dimension.
Consequently, 100% compliance with the theoretical [−1, 1] constraint
was achieved across all 23,984,128 inspected values. These results
confirm that the aggregation, scaling, and export procedures preserve
the theoretical properties of the original AlphaEarth embeddings and do
not introduce numerical artefacts that violate the expected value range.

### 5.3 Random Sampling

A random sample of 100 (LSOA, year) pairs was drawn from 400 available
pairs (50 LSOAs across eight years). For each sampled pair, the
pipeline-generated mean embedding vector was compared against the mean
embedding vector computed by direct extraction from Google Earth Engine
(GEE). The validation sample was designed to provide coverage across the
full 2017–2024 period while maintaining computational feasibility for
direct GEE extraction. Validation metrics included mean difference,
Pearson correlation, and the standard deviation of differences.
Conservative quality-assurance thresholds of ±0.1 for mean differences
and (r \> 0.5) for correlations were adopted. As demonstrated in the
following subsections, the observed results substantially exceed these
minimum requirements.

### 5.3.1 Statistical Consistency and Correlation Assessment

| Metric | Value |
|----|----|
| Total comparisons completed | 100 |
| Unique LSOAs sampled | 42 |
| Years covered | 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| Mean difference (Pipeline − EE) | −0.000049 |
| Std deviation of differences | 0.000698 |
| Mean correlation | 0.9973 |
| Min correlation | 0.9859 |
| Max correlation | 1.0000 |

| Criterion                    | Threshold | Pass Rate |
|------------------------------|-----------|-----------|
| Mean values within tolerance | ±0.1      | 100.0%    |
| Correlation above threshold  | r \> 0.5  | 100.0%    |

Agreement between the pipeline-generated values and direct Google Earth
Engine extraction was extremely high. Mean differences were negligible,
correlations consistently approached unity, and all sampled observations
exceeded the predefined validation criteria.

### 5.3.2 Systematic Bias Testing

| Test        | Value   | Result                      |
|-------------|---------|-----------------------------|
| t-statistic | −0.7085 |                             |
| p-value     | 0.4803  | ✅ PASS                     |
| Conclusion  |         | No systematic bias detected |

The mean difference between pipeline-derived values and direct Google
Earth Engine extraction was not significantly different from zero ((t =
-0.7085), (p = 0.4803)), providing no evidence of systematic bias within
the aggregation workflow.

### 5.3.3 Temporal Consistency

The yearly breakdown of mean differences and standard deviations
confirms stability across the full 2017–2024 period, with no evidence of
temporal drift:

| Year | Count | Mean Difference | Std Deviation |
|------|-------|-----------------|---------------|
| 2017 | 11    | −0.000027       | 0.000713      |
| 2018 | 13    | −0.000176       | 0.000716      |
| 2019 | 13    | 0.000040        | 0.000887      |
| 2020 | 15    | 0.000082        | 0.000602      |
| 2021 | 10    | 0.000120        | 0.000648      |
| 2022 | 10    | −0.000426       | 0.000538      |
| 2023 | 15    | −0.000018       | 0.000821      |
| 2024 | 13    | −0.000062       | 0.000605      |

Mean annual differences ranged from −0.000426 to 0.000120, while annual
standard deviations ranged from 0.000538 to 0.000887. Mean differences
remain tightly centred around zero across all years, with consistently
negligible variation and no evidence of temporal drift.

### 5.4 Visual Validation

Figure 5 provides visual confirmation of the statistical validation
results presented in Sections 5.2 and 5.3. Together, the visualisations
demonstrate strong agreement between pipeline-generated values and
direct Google Earth Engine extraction, with no evidence of systematic
bias or temporal degradation.

![validation_gee](images/validation_gee.png)

*Figure 5: Validation visualisations showing distribution of mean
differences, correlation between pipeline and Earth Engine data, and
yearly performance.*

**Top-Left Panel — Distribution of Mean Differences:** The distribution
is tightly centred around zero with no visible skew, indicating neither
dataset systematically overestimates or underestimates the other. All
values cluster within ±0.002 — well inside the ±0.1 tolerance threshold.

**Top-Right Panel — Pipeline Mean vs. EE Mean:** Near-perfect alignment
of points along the identity line demonstrates that pipeline values are
almost identical to direct Earth Engine extraction across the full value
range.

**Bottom-Left Panel — Correlation by Year:** Correlations consistently
exceed 0.99 across all eight years (well above the 0.5 threshold),
demonstrating stable data quality and extraction fidelity with no
temporal degradation.

**Bottom-Right Panel — Mean Differences by Year:** Medians cluster
tightly around zero with extremely narrow interquartile ranges,
confirming no single year exhibits systematic bias.

**Combined Validation Summary:**

| Validation Criterion            | Result                  |
|---------------------------------|-------------------------|
| Range check [−1, 1]             | 100% compliant          |
| Statistical consistency with EE | 100% pass rate          |
| Systematic bias                 | None detected           |
| Year-to-year consistency        | Stable across all years |

Collectively, the validation results demonstrate that the aggregation
workflow reproduces Google Earth Engine outputs with high fidelity,
preserves the theoretical properties of the AlphaEarth embeddings, and
maintains stable performance across the full 2017–2024 period.

## 6. Performance Evaluation

### 6.1 Runtime and Compute Performance

Processing was undertaken using a combination of Google Earth Engine
(GEE) and cloud-hosted virtual machine infrastructure. Detailed runtime
and Earth Engine Compute Unit (EECU) statistics are provided in Appendix
B.

The small-area aggregation step runs on a virtual machine with 8 CPUs
and 32 GB of memory, accessing data directly from Google Cloud Storage.
On average, processing a single year requires approximately 1.5 hours,
enabling the complete 2017–2024 dataset to be processed within
approximately one day. This demonstrates that national-scale aggregation
of the AlphaEarth embeddings can be achieved using relatively modest
cloud computing resources.

### 6.2 Storage Optimisation

The pipeline achieves significant storage reduction through three
complementary strategies:

-   **Tiling** (20 × 20 km BNG tiles), which enables parallel processing
    and avoids loading the full national dataset into memory.
-   **Int16 scaling** (multiplying float64 values by 32,767), which
    reduces per-file size by approximately one third compared to float32
    or float64 representation.
-   **LZW compression**, applied automatically to all GeoTIFF outputs.

Together these reduce the total UK dataset from an estimated \~4 TiB
(unscaled) to \~2.02 TiB across the full 2017–2024 period while
preserving the information content of the original embeddings (see
Appendix E).

### 6.3 Scalability and Reproducibility

The pipeline is designed to be fully reproducible and extensible:

-   The aggregation pipeline accepts any input GeoPackage with an
    appropriate tile ↔ polygon mapping, enabling aggregation to other
    geographies. The same methodology can therefore be applied to
    small-area statistical geographies, Middle Layer Super Output Areas
    (MSOAs), local authority districts (LADs), wards, output areas,
    bespoke study areas, and other administrative or analytical
    geographies.
-   All processing parameters are stored within configuration files,
    enabling automated year-by-year execution with minimal manual
    intervention and ensuring that identical inputs produce identical
    outputs. This supports reproducibility and facilitates the
    reprocessing of future AlphaEarth releases or alternative geographic
    boundary datasets.
-   The workflow is inherently parallelisable because geographic units
    are processed independently. Consequently, runtime can be reduced
    through the allocation of additional computational resources,
    subject to available memory and storage constraints. Performance can
    be improved by increasing the number of Dask workers, provided
    sufficient virtual machine memory is available.

## 7. Usage Notes and Limitations

### 7.1 Intended Applications

The Imago Embedding data product is intended for use in:

-   Small-area socioeconomic and environmental analysis using
    satellite-derived features.

-   Machine learning and statistical modelling tasks requiring
    area-level environmental representations.

-   Similarity analysis, clustering, and dimensionality reduction of
    neighbourhood-scale environments.

-   Environmental and built-environment characterisation using latent
    representations derived from Earth observation imagery.

-   Change detection and temporal trend analysis at small-area
    statistical geography level (2017–2024).

-   Integration with administrative data (e.g., deprivation indices,
    Census data, health statistics, and environmental indicators)

-   Research and policy applications requiring a spatially
    comprehensive, temporally consistent feature set for UK small-area
    statistical geographies.

### 7.2 Recommended Analytical Practices

-   When using the Int16-scaled intermediate data, apply the descaling
    formula

    $$x_\text{original} = \frac{x_\text{int16}}{32767}$$

    before analysis to recover the original [−1, 1] range.

-   Embedding dimensions should generally be interpreted collectively
    rather than individually. Individual dimensions do not correspond to
    specific physical, environmental, or socioeconomic variables, and
    their analytical value arises primarily from the relationships among
    dimensions within the full embedding vector.

-   For aggregation to other geographies (e.g., MSOA), ensure the input
    GeoPackage contains an appropriate tile ↔ polygon mapping consistent
    with the 20 × 20 km BNG tile grid.

-   Temporal changes in embedding values should be interpreted as
    changes in the latent representation of the observed environment
    rather than direct measurements of specific environmental,
    land-cover, or socioeconomic changes.

### 7.3 Known Limitations

Several limitations should be considered when using the data product.

-   **Partial-pixel boundary effects:** The current pipeline uses
    `rasterio` for zonal statistics, which treats all overlapping pixels
    as contributing equally (no partial-pixel weighting). This
    introduces a small positive bias in mean values for small,
    high-density geographies where the proportion of
    boundary-intersecting pixels is higher. The 10-metre resolution
    substantially mitigates this effect, but it remains a known source
    of minor imprecision.
-   **Random sampling validation scope:** The sampling validation was
    limited to 100 (geographic unit, year) pairs from 400 available, and
    focuses on statistical consistency rather than exact pixel-level
    matching. Different aggregation methods may produce slightly
    different values.
-   **Data quality:** Although data quality issues affecting 2017
    (related to Sentinel-1 image dropout) have been addressed in the
    current GEE collection, users should be aware of this history when
    using 2017 data.

## 8. Discussion

### 8.1 Scientific and Policy Implications

The Imago Embedding data product makes satellite-derived environmental
representations accessible at the standard UK small-area geography for
the first time at national scale and annual temporal resolution. This
product helps bridge the gap between raw Earth observation data and
administrative statistical geographies, enabling a new class of analyses
that combine satellite-derived features with socioeconomic, health,
housing, environmental, and demographic data available at the scale of
small statistical areas. By providing annual, nationally consistent
environmental representations, the data product creates opportunities
for longitudinal analyses of neighbourhood change, environmental
inequalities, urban development, and place-based policy interventions
that would otherwise require substantial Earth observation expertise and
computational resources.

The strong agreement between pipeline-derived values and direct Google
Earth Engine extraction provides confidence that the product can be used
in downstream statistical, machine-learning, and policy applications
without introducing substantial aggregation artefacts.

### 8.2 Methodological Contributions

The workflow demonstrates a scalable approach for transforming
national-scale Earth observation foundation model outputs into
small-area statistical geography datasets suitable for research and
policy applications. The tile-aware weighted averaging procedure for
multi-tile geographic units ensures that areas intersecting tile
boundaries receive spatially representative embedding values while
maintaining computational efficiency at national scale. Similarly, the
Int16 scaling strategy preserves embedding values with negligible
numerical error while substantially reducing storage requirements,
demonstrating a practical approach for managing large Earth observation
datasets. Together with automated Google Earth Engine extraction and
comprehensive validation, these components provide a reproducible
framework that can be adapted to future embedding products and
alternative geographic boundaries.

### 8.3 Future Development Opportunities

-   **Expanded temporal coverage:** Extension of the pipeline to
    accommodate new years of the Google Satellite Embedding dataset as
    they become available.
-   **Additional geographies:** Production of equivalent datasets for
    MSOAs, wards, local authority districts, and other administrative
    units.
-   **Additional foundation models:** Extension of the workflow to
    alternative Earth observation embedding products and foundation
    models.
-   **Temporal consistency checks:** Year-over-year plausibility checks
    and outlier detection for individual LSOA time series.
-   **Derived products and analytical tools**: Development of
    dimensionality-reduced representations, similarity-search tools, and
    derived indicators to support wider adoption by research and policy
    communities.
-   **Windowed reads:** Implementation of true windowed rasterio reads
    to reduce memory pressure and enable higher parallelism in the LSOA
    aggregation step.

------------------------------------------------------------------------

## 9. Data and Code Availability

### 9.1 Data Access

The validated small area statistical geography satellite embedding
dataset (2017–2024) is published via the Imago Data Catalogue:
[https://data.imago.ac.uk/datasets/google-satellite-embedding-v1-small-areas-20](https://data.imago.ac.uk/datasets/google-satellite-embedding-v1-small-areas-2017-2024){.uri}

The catalogue entry includes the annual GeoPackage datasets, metadata,
documentation, and supporting resources required for data use and
interpretation.

### 9.2 Code and Workflow Availability

The source code is available on [Imago
Github](https://github.com/Imago-SDRUK/EMBED2Social) repository.

The pipeline comprises two main scripts:

-   `src/download_ee.py` — GEE export CLI tool (see Appendix A for full
    usage)
-   `src/embed_to_lsoa.py` — small-area aggregation workflow aggregation
    pipeline

Supporting configuration files, templates, and workflow documentation
are provided to facilitate reproducibility and adaptation to alternative
geographies.

### 9.3 Licensing

The data product is released under the Creative Commons Attribution 4.0
International (CC BY 4.0) licence, permitting use, redistribution, and
adaptation provided appropriate attribution is given.

The source code is released under the licence specified within the
GitHub repository.

## 10. Conclusion

This report has described the development, methodology, and validation
of the Imago small-area statistical geography satellite embedding data
product for the United Kingdom, covering 2017 to 2024. The product
provides 64-dimensional, L2-normalised embedding vectors for 46,844
small-area statistical geographies annually, derived from the Google
Satellite Embedding Dataset V1 through an automated workflow comprising
Google Earth Engine data extraction, intermediate data preparation, and
small-area aggregation. Validation confirmed 100% compliance with the
theoretical [−1, 1] embedding value range across approximately 24
million values and demonstrated near-perfect agreement (mean (r =
0.997); mean difference = $-4.95 \times 10^{-5}$ with direct Google
Earth Engine extraction. No evidence of systematic bias was detected,
and workflow performance remained stable across the full 2017–2024
period.

The data product is published via the Imago Data Catalogue and is
intended to support a wide range of small-area analytical, research, and
policy applications. By transforming national-scale Earth observation
foundation model outputs into accessible geographic-unit
representations, the product helps bridge the gap between Earth
observation data and administrative statistical geographies, creating
new opportunities for environmental, socioeconomic, health, housing, and
policy research. Future development may focus on enhanced boundary
handling, additional embedding products and foundation models, derived
analytical products, and automated validation workflows for future
annual releases.

## Acknowledgements

This data product was developed as part of the EMBED2Social – Embedding
Embeddings Across Social Research and Policy project, funded through the
Smart Data Research UK (SDR UK) Research Grant programme by the Economic
and Social Research Council (Grant Reference: ES/Z504208/1) in
collaboration with the Ministry of Housing, Communities & Local
Government AI Directorate.

------------------------------------------------------------------------

## References

Key sources:

-   Google Satellite Embedding Dataset V1:
    <https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL>
-   Google Earth Engine blog post on the Satellite Embedding Dataset:
    <https://medium.com/google-earth/ai-powered-pixels-introducing-googles-satellite-embedding-dataset-31744c1f4650>
-   Source Cooperative AlphaEarth Foundation Embeddings:
    <https://source.coop/tge-labs/aef>
-   GEE Computation Overview (stability and predictability):
    <https://developers.google.com/earth-engine/guides/computation_overview#stability_and_predictability>
-   London Datastore statistical GIS boundary files:
    <https://data.london.gov.uk/dataset/statistical-gis-boundary-files-for-london-20od9/>

------------------------------------------------------------------------

## Appendices

### Appendix A: Command-Line Tool Configuration and Usage Examples

The GEE export pipeline is invoked via:

``` bash
python src/download_ee.py
```

Additional help and usage examples:

``` bash
python src/download_ee.py --help
```

Positional arguments are not used; the CLI uses named options only. The
following options are available:

| Option | Description | Default |
|------------------------|------------------------|------------------------|
| `--collection` | Earth Engine image collection to extract | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` |
| `--project`, `-p` | Google Earth Engine project ID | `imago` |
| `--auth-mode` | Earth Engine authentication mode | `gcloud` |
| `--tiles` | Path to the gridded area of interest (tiles) | `data/uk_1km_grid_sample1.gpkg` |
| `--storage` | Export destination – Google Cloud Storage or Google Drive | `cloud` |
| `--folder` | Cloud Storage bucket or Google Drive folder | `embed2social-storage` |
| `--year`, `-y` | Year to extract dataset for | `2024` |
| `--verbose`, `-v` | Enable verbose logging (WARNING: can produce very large logs) | `False` |
| `--cog` | Export as Cloud Optimised GeoTIFF (COG) | `False` |
| `--crs` | Coordinate Reference System (CRS) of the output | `EPSG:27700` |
| `--res` | Spatial resolution of output | `10` |
| `--scale` | Scale to Int16, multiplying by 32,767 | `False` |

Any annual collections can be used as input for further export — for
example, [ESA WorldCover 10m
v100](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100)
or [ESA WorldCereal Active Cropland 10 m
v100](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCereal_2021_MARKERS_v100).
Datasets with finer temporal granularity than annual will not be
correctly aggregated by this tool.

------------------------------------------------------------------------

### Appendix B: Detailed Runtime Benchmarking Tables

Full GEE pipeline runtime and EECU time by year:

| Year | Pipeline runtime (s) | Pipeline runtime (h) | EECU time (s) | EECU time (h) | Total size (GB) |
|:-----------|:-----------|:-----------|:-----------|:-----------|:-----------|
| 2024 | 27,420.6247 | 7.6168 | 278,886.6827 | 77.4685 | 258.24 |
| 2023 | 30,263.8161 | 8.4066 | 264,226.6384 | 73.3962 | 258.64 |
| 2022 | 25,515.9630 | 7.0877 | 257,439.4404 | 71.5109 | 258.64 |
| 2021 | 27,541.3252 | 7.6504 | 262,592.8037 | 72.9424 | 258.48 |
| 2020 | 24,354.6962 | 6.7652 | 275,837.1997 | 76.6214 | 258.76 |
| 2019 | 41,363.0000 | 11.4892 | 302,880.4143 | 84.1334 | 258.11 |
| 2018 | 32,771.5112 | 9.1032 | 262,321.2517 | 72.8670 | 258.44 |
| 2017 | 42,716.2087 | 11.8656 | 287,451.6494 | 79.8477 | 260.33 |
| **AVERAGE** | 31,493.3931 | 8.7482 | 273,954.51 | 76.0985 | 258.705 |
| **TOTAL** | 251,947.145 | **69.9853** | 2,191,636.08 | **608.7877** | **2.02 TiB** |

Notes:

-   Pipeline runtime is client wall-clock time, while EECU time reflects
    billable compute.
-   EECU variability factor is up to 2.8× for identical requests.
-   Total runtime variability factor is up to 8.8×.
-   LSOA aggregation runtime is \~1.5 hours per year (8 CPUs, 32 GB RAM,
    GCS-mounted storage).

------------------------------------------------------------------------

### Appendix C: Full Validation Results and Supplementary Statistics

**Range Validation Summary**

All 24 million values (46,844 LSOAs × 64 dimensions × 8 years) passed
the [−1, 1] range check with zero out-of-range values.

**Random Sampling Validation — Full Results**

| Metric                          | Value     |
|---------------------------------|-----------|
| Total comparisons completed     | 100       |
| Unique LSOAs sampled            | 42        |
| Years covered                   | 2017–2024 |
| Mean difference (Pipeline − EE) | −0.000049 |
| Std deviation of differences    | 0.000698  |
| Mean correlation                | 0.9973    |
| Min correlation                 | 0.9859    |
| Max correlation                 | 1.0000    |
| t-statistic                     | −0.7085   |
| p-value                         | 0.4803    |
| Systematic bias detected        | No        |

**Yearly Breakdown**

| Year | Count | Mean Difference | Std Deviation |
|------|-------|-----------------|---------------|
| 2017 | 11    | −0.000027       | 0.000713      |
| 2018 | 13    | −0.000176       | 0.000716      |
| 2019 | 13    | 0.000040        | 0.000887      |
| 2020 | 15    | 0.000082        | 0.000602      |
| 2021 | 10    | 0.000120        | 0.000648      |
| 2022 | 10    | −0.000426       | 0.000538      |
| 2023 | 15    | −0.000018       | 0.000821      |
| 2024 | 13    | −0.000062       | 0.000605      |

------------------------------------------------------------------------

### Appendix D: Complete Output Schema and Field Descriptions

The output GeoPackage contains the following fields per row (one row =
one LSOA × one year):

| Field | Type | Description |
|------------------------|------------------------|------------------------|
| data_zone_code | String | ONS LSOA (Lower layer Super Output Area) code for England and Wales, or equivalent data zone code for Scotland and Northern Ireland, representing the spatial area at which cloud probability is aggregated. |
| Geometry | MultiPolygon | MultiPolygon geometry representing the LSOA / data zone boundaries, stored in WKBGeometry format. |
| `band1_mean` … `band64_mean` | Float64 | Mean embedding value per dimension across all valid pixels in the LSOA |

Additional fields (median, min, max, std, sum per dimension) can be
produced by the pipeline on request. Embedding values are in the [−1, 1]
range (after descaling if the Int16 intermediate format is used).

> Although 2017 featured data quality issues (see
> [here](https://source.coop/tge-labs/aef)), they have been addressed in
> the latest version of the original Embedding data collection available
> on Google Earth Engine. The issue was related to dropout of some
> Sentinel-1 images, but the overall impact on dataset accuracy was
> quite low. As a rule of thumb, Google Earth Engine data is a source of
> truth and always contains the latest and updated version.

------------------------------------------------------------------------

### Appendix E: Scaling Precision Analysis (Including Error Statistics)

The Int16 scaling operation maps float64 values in [−1, +1] to integers
in [−32767, +32767] via:

$$x_\text{int16} = \text{round}(x_\text{float64} \times 32767)$$

To recover original values:

$$x_\text{original} = \frac{x_\text{int16}}{32767}$$

**Imago scaling:**

| Tile      | Band | Max_err  | Mean_err | RMSE     |
|-----------|------|----------|----------|----------|
| SJ26-2024 | 1    | 0.000015 | 0.000008 | 0.000009 |
| SJ26-2024 | 2    | 0.000015 | 0.000007 | 0.000009 |
| SJ26-2024 | 3    | 0.000015 | 0.000008 | 0.000009 |
| SJ26-2024 | 4    | 0.000015 | 0.000007 | 0.000008 |
| SJ26-2024 | 5    | 0.000015 | 0.000007 | 0.000008 |

**Source Cooperative scaling:**

| Tile      | Band | Max_err  | Mean_err | RMSE     |
|-----------|------|----------|----------|----------|
| S084-2024 | 1    | 0.090058 | 0.000044 | 0.000898 |
| S084-2024 | 2    | 0.104760 | 0.000053 | 0.001083 |
| S084-2024 | 3    | 0.121553 | 0.000062 | 0.001264 |
| S084-2024 | 4    | 0.109496 | 0.000054 | 0.001218 |
| S084-2024 | 5    | 0.077017 | 0.000035 | 0.000713 |

**Comparison**

| Statistic | IMAGO (Int16) | Source Cooperative (Int8) |
|----|----|----|
| Mean error | \~10⁻⁶ (6th decimal place) | Higher |
| RMSE | \~10⁻⁶ (6th decimal place) | Higher |
| Maximum absolute error | \~10⁻⁵ (5th decimal place) | Higher |

The IMAGO Int16 scaling preserves float64 values with a maximum error of
sub-5th decimal place, which is negligible for all intended analytical
applications. The Source Cooperative Int8 distribution, while more
compact, has lower precision, particularly regarding maximum absolute
error.

> Testing with GEE export in verbose mode revealed that the original
> Embedding tiling differs from the published Source Cooperative tile
> boundaries. For example, an area of interest intersecting four Source
> Cooperative tiles may overlay only two original Google Satellite
> Embedding images, while the output remains consistent and covers the
> entire area of interest.

*See Figure 3 in the main text for visual comparison of scaling error
distributions*
