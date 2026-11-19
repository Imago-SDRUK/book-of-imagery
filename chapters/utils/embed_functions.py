# @title
"""
Utility functions for working with LSOA-level satellite image embeddings.

This module includes functions for:
- filtering and selecting embedding data
- clustering LSOAs in embedding space
- static and interactive mapping
- finding representative LSOAs within clusters
- plotting embedding-space distances
- training and evaluating a Random Forest classifier
- preparing variables for mapped comparison
- displaying two interactive maps side by side
"""

# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------

import re

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from folium.features import DivIcon
from IPython.display import HTML, display
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------------------
# Data preparation and clustering
# ---------------------------------------------------------------------

def filter_table(gdf):
    """
    Keep identifier columns, embedding variables, and geometry.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame containing identifiers, embedding variables,
        and geometry.

    Returns
    -------
    geopandas.GeoDataFrame
        Filtered GeoDataFrame containing available identifier columns,
        embedding columns, and geometry.
    """
    id_cols = ["data_zone_code", "country", "LSOA21CD", "LSOA21NM"]
    embedding_cols = [c for c in gdf.columns if c.endswith("_mean")]

    cols = [c for c in id_cols if c in gdf.columns] + embedding_cols

    if "geometry" in gdf.columns:
        cols.append("geometry")

    return gdf[cols]


def get_embedding_cols(gdf, pattern=r"^A\d+_mean$"):
    """
    Return embedding column names sorted by numeric index.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing embedding variables.
    pattern : str, optional
        Regular expression pattern used to select embedding columns.

    Returns
    -------
    list of str
        Sorted embedding column names.

    Raises
    ------
    ValueError
        If no columns match `pattern`.
    """
    cols = [c for c in gdf.columns if re.match(pattern, c)]
    if not cols:
        raise ValueError("No embedding columns found matching pattern like A##_mean.")

    return sorted(cols, key=lambda x: int(re.findall(r"\d+", x)[0]))


def kmeans_clustering(gdf, k, feature_suffix="_mean", random_state=42):
    """
    Cluster LSOAs using embedding variables and k-means.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame containing embedding variables.
    k : int
        Number of clusters.
    feature_suffix : str, optional
        Suffix used to identify feature columns. Default is "_mean".
    random_state : int, optional
        Random seed for reproducibility. Default is 42.

    Returns
    -------
    geopandas.GeoDataFrame
        Copy of `gdf` with an added "cluster" column.

    Raises
    ------
    ValueError
        If no feature columns are found that match `feature_suffix`.
    """
    if not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer.")

    feature_cols = [c for c in gdf.columns if c.endswith(feature_suffix)]
    if not feature_cols:
        raise ValueError(f"No feature columns found ending with '{feature_suffix}'.")

    X = gdf[feature_cols].to_numpy(dtype=float)

    kmeans = KMeans(n_clusters=k, random_state=random_state)

    gdf_out = gdf.copy()
    gdf_out["cluster"] = kmeans.fit_predict(X)
    return gdf_out


def show_cluster_labels(gdf, cluster_col="cluster"):
    """
    Print the unique cluster labels.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing cluster labels.
    cluster_col : str, optional
        Name of the cluster label column. Default is "cluster".

    Raises
    ------
    ValueError
        If `cluster_col` is not present in `gdf`.
    """
    if cluster_col not in gdf.columns:
        raise ValueError(f"'{cluster_col}' column not found.")

    labels = sorted(pd.unique(gdf[cluster_col]))
    print("Your clusters are:", ", ".join(map(str, labels)))


# ---------------------------------------------------------------------
# Static mapping
# ---------------------------------------------------------------------

def plot_simple_map(
    gdf,
    cluster_col="cluster",
    title="Unsupervised Classification of Places in London",
    figsize=(8, 8),
    legend=True,
):
    """
    Plot clusters on a simple choropleth map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing geometries and cluster labels.
    cluster_col : str, optional
        Name of the cluster label column. Default is "cluster".
    title : str, optional
        Plot title.
    figsize : tuple of int, optional
        Figure size in inches. Default is (8, 8).
    legend : bool, optional
        Whether to show a legend. Default is True.

    Returns
    -------
    matplotlib.axes.Axes
        Axes containing the map.

    Raises
    ------
    ValueError
        If `cluster_col` is not present in `gdf`.
    """
    if cluster_col not in gdf.columns:
        raise ValueError(f"'{cluster_col}' column not found.")

    fig, ax = plt.subplots(figsize=figsize)
    gdf.plot(column=cluster_col, categorical=True, legend=legend, ax=ax)
    ax.set_title(title)
    ax.axis("off")
    return ax


# ---------------------------------------------------------------------
# Interactive mapping helpers
# ---------------------------------------------------------------------

def parse_reference_points(text):
    """
    Parse reference points from a simple text format.

    Each line must be formatted as:
    "Name", latitude, longitude

    Parameters
    ----------
    text : str or None
        Multiline string containing one reference point per line.

    Returns
    -------
    list of dict
        List of dictionaries with keys "name", "lat", and "lon".

    Raises
    ------
    ValueError
        If a line does not contain exactly three comma-separated values.
    """
    reference_points = []

    if not text:
        return reference_points

    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            raise ValueError(f"Invalid line format: {line}")

        reference_points.append(
            {
                "name": parts[0].strip('"').strip("'"),
                "lat": float(parts[1]),
                "lon": float(parts[2]),
            }
        )

    return reference_points


def make_webmap_general(
    focus_gdf,
    focus_col=None,
    focus_name="Focus",
    focus_tooltip_cols=(),
    focus_categorical=True,
    focus_legend=True,
    focus_cmap="Set1",
    focus_style_kwds=None,
    context_gdf=None,
    context_name="Context",
    context_style_kwds=None,
    pois=None,
    layer_control_collapsed=False,
    fit_to="focus",
    zoom_start=10,
):
    """
    Create an interactive Folium map with a focus layer and an optional context layer.

    Parameters
    ----------
    focus_gdf : geopandas.GeoDataFrame
        GeoDataFrame to display as the main layer.
    focus_col : str or None, optional
        Column used to colour polygons in the focus layer.
    focus_name : str, optional
        Layer name for the focus layer.
    focus_tooltip_cols : tuple of str, optional
        Columns shown in the tooltip for the focus layer.
    focus_categorical : bool, optional
        Whether `focus_col` should be treated as categorical.
    focus_legend : bool, optional
        Whether to show a legend for the focus layer.
    focus_cmap : str, optional
        Colour map name used by GeoPandas.
    focus_style_kwds : dict or None, optional
        Style arguments for the focus layer.
    context_gdf : geopandas.GeoDataFrame or None, optional
        Optional context layer displayed underneath the focus layer.
    context_name : str, optional
        Layer name for the context layer.
    context_style_kwds : dict or None, optional
        Style arguments for the context layer.
    pois : str or None, optional
        Multiline string of reference points parsed by `parse_reference_points`.
    layer_control_collapsed : bool, optional
        Whether the layer control is collapsed.
    fit_to : {"focus", "all"}, optional
        Whether to fit bounds to the focus layer only or to all displayed layers.
    zoom_start : int, optional
        Initial zoom level before fit bounds are applied.

    Returns
    -------
    folium.Map
        Interactive map.

    Raises
    ------
    ValueError
        If inputs are invalid or if the GeoDataFrames have no CRS.
    """
    # Validate main inputs
    if focus_gdf is None or len(focus_gdf) == 0:
        raise ValueError("focus_gdf must be a non-empty GeoDataFrame.")

    if fit_to not in {"focus", "all"}:
        raise ValueError("fit_to must be either 'focus' or 'all'.")

    if focus_col is not None and focus_col not in focus_gdf.columns:
        raise ValueError(f"'{focus_col}' column not found in focus_gdf.")

    # Set default styles if none are provided
    if focus_style_kwds is None:
        focus_style_kwds = {"fillOpacity": 0.6, "weight": 0.8, "color": "black"}

    if context_style_kwds is None:
        context_style_kwds = {
            "fillOpacity": 0.05,
            "opacity": 0.6,
            "weight": 0.6,
            "color": "grey",
        }

    # Check CRS before reprojection
    if focus_gdf.crs is None:
        raise ValueError(
            "focus_gdf has no CRS. Set it first, for example with "
            "focus_gdf = focus_gdf.set_crs(epsg=4326)"
        )

    if context_gdf is not None and context_gdf.crs is None:
        raise ValueError(
            "context_gdf has no CRS. Set it first, for example with "
            "context_gdf = context_gdf.set_crs(epsg=4326)"
        )

    # Reproject layers to WGS84 for Folium
    focus_wgs84 = focus_gdf.to_crs(epsg=4326)
    context_wgs84 = context_gdf.to_crs(epsg=4326) if context_gdf is not None else None

    # Centre the map using the focus layer extent
    minx, miny, maxx, maxy = focus_wgs84.total_bounds
    centre = [(miny + maxy) / 2, (minx + maxx) / 2]

    # Create base Folium map
    m = folium.Map(location=centre, zoom_start=zoom_start, tiles=None)

    # Add basemap options
    folium.TileLayer(
        "CartoDB positron",
        name="CartoDB Positron",
        overlay=False,
        control=True,
        show=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri",
        name="Satellite (Esri)",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Add optional context layer beneath the focus layer
    if context_wgs84 is not None and len(context_wgs84) > 0:
        context_wgs84.explore(
            m=m,
            name=context_name,
            tooltip=False,
            legend=False,
            show=True,
            style_kwds=context_style_kwds,
        )

    # Prepare tooltip fields for the focus layer
    tooltip = [c for c in focus_tooltip_cols if c in focus_wgs84.columns]

    # Add focus layer
    if focus_col is None:
        focus_wgs84.explore(
            m=m,
            name=focus_name,
            tooltip=tooltip if tooltip else False,
            legend=False,
            style_kwds=focus_style_kwds,
        )
    else:
        focus_wgs84.explore(
            m=m,
            column=focus_col,
            categorical=bool(focus_categorical),
            legend=bool(focus_legend),
            tooltip=tooltip if tooltip else False,
            cmap=focus_cmap,
            name=focus_name,
            style_kwds=focus_style_kwds,
        )

    # Add optional reference points and labels
    reference_points = parse_reference_points(pois)
    if reference_points:
        ref_layer = folium.FeatureGroup(name="Reference points", show=False)
        label_layer = folium.FeatureGroup(name="Reference point names", show=False)

        for pt in reference_points:
            folium.Marker(
                [pt["lat"], pt["lon"]],
                popup=pt["name"],
                tooltip=pt["name"],
                icon=folium.Icon(icon="info-sign"),
            ).add_to(ref_layer)

            folium.Marker(
                [pt["lat"], pt["lon"]],
                icon=DivIcon(
                    html=f"<div style='font-size:12px;font-weight:600;'>{pt['name']}</div>"
                ),
            ).add_to(label_layer)

        ref_layer.add_to(m)
        label_layer.add_to(m)

    # Add layer control
    folium.LayerControl(collapsed=layer_control_collapsed).add_to(m)

    # Fit map to requested extent
    bounds_gdf = (
        context_wgs84
        if fit_to == "all" and context_wgs84 is not None and len(context_wgs84) > 0
        else focus_wgs84
    )

    minx, miny, maxx, maxy = bounds_gdf.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(10, 10))

    return m


# ---------------------------------------------------------------------
# Cluster-centroid analysis
# ---------------------------------------------------------------------

def closest_lsoas_to_cluster(
    gdf,
    cluster_number,
    n_closest=5,
    cluster_col="cluster",
    id_cols=("LSOA21CD", "LSOA21NM"),
):
    """
    Find the LSOAs closest to the centroid of a selected cluster in embedding space.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing embedding variables and cluster labels.
    cluster_number : int
        Cluster label to analyse.
    n_closest : int, optional
        Number of closest LSOAs to return.
    cluster_col : str, optional
        Name of the cluster label column.
    id_cols : tuple of str, optional
        Identifier columns to keep in the output.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing identifier columns, cluster label,
        distance to the cluster centroid, and geometry.

    Raises
    ------
    ValueError
        If inputs are missing or invalid.
    """
    if cluster_col not in gdf.columns:
        raise ValueError(f"'{cluster_col}' column not found.")
    if not isinstance(n_closest, int) or n_closest <= 0:
        raise ValueError("n_closest must be a positive integer.")

    emb_cols = get_embedding_cols(gdf)

    mask = gdf[cluster_col] == cluster_number
    if int(mask.sum()) == 0:
        raise ValueError(f"No rows found for {cluster_col} == {cluster_number}.")

    g = gdf.loc[mask].copy()

    # Compute the cluster centroid and Euclidean distances in embedding space
    centroid = np.nanmean(g[emb_cols].to_numpy(dtype=float), axis=0)
    X = g[emb_cols].to_numpy(dtype=float)
    distances = np.linalg.norm(X - centroid, axis=1)

    n_use = min(n_closest, len(g))
    idx = np.argsort(distances)[:n_use]

    out = g.iloc[idx].copy()
    out["distance"] = distances[idx]
    out = out.sort_values("distance")

    keep = [c for c in id_cols if c in out.columns] + [cluster_col, "distance", "geometry"]
    return out[[c for c in keep if c in out.columns]]


def map_closest_lsoas(
    gdf,
    cluster_number,
    n_closest,
    context_gdf=None,
    cluster_col="cluster",
    tooltip_cols=("LSOA21CD", "LSOA21NM", "distance"),
    fill_opacity=0.6,
    weight=2.0,
    edge_color="black",
    pois=None,
):
    """
    Map the LSOAs closest to a selected cluster centroid in embedding space.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame containing embedding variables and cluster labels.
    cluster_number : int
        Cluster label to analyse.
    n_closest : int
        Number of closest LSOAs to display.
    context_gdf : geopandas.GeoDataFrame or None, optional
        Optional context layer shown beneath the selected LSOAs.
    cluster_col : str, optional
        Name of the cluster label column.
    tooltip_cols : tuple of str, optional
        Columns shown in the tooltip.
    fill_opacity : float, optional
        Polygon fill opacity.
    weight : float, optional
        Polygon border width.
    edge_color : str, optional
        Polygon border colour.
    pois : str or None, optional
        Optional reference points text.

    Returns
    -------
    tuple
        A tuple containing:
        - folium.Map
        - geopandas.GeoDataFrame of closest LSOAs
    """
    closest_gdf = closest_lsoas_to_cluster(
        gdf=gdf,
        cluster_number=cluster_number,
        n_closest=n_closest,
        cluster_col=cluster_col,
    )

    # Rank the selected LSOAs so they can be coloured distinctly on the map
    closest_gdf = closest_gdf.copy()
    closest_gdf["rank"] = range(1, len(closest_gdf) + 1)

    m = make_webmap_general(
        focus_gdf=closest_gdf,
        focus_col="rank",
        focus_name=f"{len(closest_gdf)} closest LSOAs",
        focus_tooltip_cols=tooltip_cols,
        focus_categorical=True,
        focus_legend=True,
        focus_cmap="Set1",
        focus_style_kwds={
            "fillOpacity": float(fill_opacity),
            "opacity": 1.0,
            "weight": float(weight),
            "color": edge_color,
        },
        context_gdf=context_gdf,
        context_name="Context (all LSOAs)",
        context_style_kwds={
            "fillOpacity": 0.05,
            "opacity": 0.6,
            "weight": 0.6,
            "color": "grey",
        },
        pois=pois,
        fit_to="focus",
        layer_control_collapsed=False,
        zoom_start=12,
    )

    return m, closest_gdf


def plot_embedding_distances(
    df,
    distance_col="distance",
    label_col="LSOA21NM",
    title="Distances of Closest LSOAs in Embedding Space",
    figsize=(9, 4),
):
    """
    Plot embedding-space distances in ascending order.

    Parameters
    ----------
    df : pandas.DataFrame or geopandas.GeoDataFrame
        DataFrame containing distance values and labels.
    distance_col : str, optional
        Column containing embedding-space distances.
    label_col : str, optional
        Column used for top x-axis labels.
    title : str, optional
        Plot title.
    figsize : tuple of int, optional
        Figure size in inches.

    Returns
    -------
    matplotlib.axes.Axes
        Axes object containing the plot.

    Raises
    ------
    ValueError
        If required columns are not present in `df`.
    """
    if distance_col not in df.columns:
        raise ValueError(f"'{distance_col}' column not found.")
    if label_col not in df.columns:
        raise ValueError(f"'{label_col}' column not found.")

    df_sorted = df.sort_values(distance_col).reset_index(drop=True)

    x = range(1, len(df_sorted) + 1)
    distances = df_sorted[distance_col]
    labels = df_sorted[label_col]

    fig, ax = plt.subplots(figsize=figsize)

    # Plot distances from closest to farthest
    ax.plot(x, distances, marker="o")
    ax.set_xlabel("Rank (closest to farthest)")
    ax.set_ylabel("Distance to cluster centroid")
    ax.set_title(title)
    ax.grid(True)

    # Show area names on a secondary top axis
    ax_top = ax.secondary_xaxis("top")
    ax_top.set_xticks(list(x))
    ax_top.set_xticklabels(labels, rotation=45, ha="left", fontsize=8)
    ax_top.set_xlabel(label_col)

    plt.tight_layout()
    return ax


# ---------------------------------------------------------------------
# Classification modelling
# ---------------------------------------------------------------------

def run_rf_classifier(
    data,
    y_col,
    x_cols,
    test_size=0.2,
    random_state=42,
    n_estimators=500,
    n_jobs=-1,
    class_weight="balanced",
    dropna=True,
    treat_y_as_ordered=True,
    verbose=True,
):
    """
    Train and evaluate a Random Forest classifier.

    Parameters
    ----------
    data : pandas.DataFrame or geopandas.GeoDataFrame
        Input dataset containing the target and predictor variables.
    y_col : str
        Name of the target variable column.
    x_cols : list of str
        Names of the predictor variable columns.
    test_size : float, optional
        Proportion of data used for testing.
    random_state : int, optional
        Random seed for reproducibility.
    n_estimators : int, optional
        Number of trees in the forest.
    n_jobs : int, optional
        Number of CPU cores to use.
    class_weight : str, dict, or None, optional
        Class weighting strategy.
    dropna : bool, optional
        If True, drop rows with missing values in the target or predictors.
    treat_y_as_ordered : bool, optional
        If True, convert the target to ordered integer codes before modelling.
    verbose : bool, optional
        If True, print evaluation results.

    Returns
    -------
    dict
        Dictionary containing model outputs, predictions, metrics,
        and feature importances.

    Raises
    ------
    ValueError
        If required columns are missing, no rows remain after filtering,
        or the target has fewer than two classes.
    """
    if y_col not in data.columns:
        raise ValueError(f"Target column '{y_col}' not found.")
    if not x_cols:
        raise ValueError("x_cols must contain at least one predictor column.")

    missing = [c for c in [y_col] + list(x_cols) if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if not 0 < float(test_size) < 1:
        raise ValueError("test_size must be between 0 and 1.")

    # Prepare model table
    df = data[[y_col] + list(x_cols)].copy()
    if dropna:
        df = df.dropna()

    if df.empty:
        raise ValueError("No rows available after filtering or dropping missing values.")

    y_raw = df[y_col]
    X = df[list(x_cols)]

    # Optionally encode the target as ordered integer classes
    if treat_y_as_ordered:
        y_cat = pd.Categorical(y_raw, ordered=True)
        if (y_cat.codes < 0).any():
            raise ValueError("Target contains missing or invalid categories after conversion.")
        y = pd.Series(y_cat.codes, index=df.index) + 1
        y_categories = y_cat.categories
    else:
        y = y_raw.copy()
        y_categories = None

    if pd.Series(y).nunique() < 2:
        raise ValueError("Target must contain at least two classes for classification.")

    # Split data, preserving class proportions where possible
    stratify = y if pd.Series(y).nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=float(test_size),
        random_state=random_state,
        stratify=stratify,
    )

    # Train model
    rf = RandomForestClassifier(
        n_estimators=int(n_estimators),
        random_state=random_state,
        n_jobs=n_jobs,
        class_weight=class_weight,
    )
    rf.fit(X_train, y_train)

    # Predict labels and class probabilities
    y_pred = rf.predict(X_test)
    pred_probs_df = pd.DataFrame(
        rf.predict_proba(X_test),
        columns=rf.classes_,
        index=X_test.index,
    )

    # Compute summary metrics
    acc = accuracy_score(y_test, y_pred)

    try:
        mae_ordinal = (
            pd.Series(y_pred, index=X_test.index) -
            pd.Series(y_test, index=X_test.index)
        ).abs().mean()
    except Exception:
        mae_ordinal = None

    confusion = pd.crosstab(
        pd.Series(y_test, name=f"Actual {y_col}"),
        pd.Series(y_pred, name=f"Predicted {y_col}"),
    )

    importances = pd.Series(
        rf.feature_importances_,
        index=list(x_cols),
        name="importance",
    ).sort_values(ascending=False)

    if verbose:
        print(f"Test accuracy: {acc:.3f}")
        if mae_ordinal is not None:
            print(f"Mean absolute label error: {mae_ordinal:.2f}")
        print("\nConfusion matrix:")
        print(confusion)
        print("\nTop 15 feature importances:")
        print(importances.head(15))

    return {
        "model": rf,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "y_pred": y_pred,
        "pred_probs": pred_probs_df,
        "accuracy": acc,
        "mae_ordinal": mae_ordinal,
        "confusion": confusion,
        "importances": importances,
        "y_categories": y_categories,
    }


def plot_feature_importance(
    importances,
    top_n=15,
    title="Top Feature Importances",
    figsize=(6, 5),
):
    """
    Plot the top N feature importances.

    Parameters
    ----------
    importances : pandas.Series
        Feature importances indexed by feature name.
    top_n : int, optional
        Number of top features to display.
    title : str, optional
        Plot title.
    figsize : tuple of int, optional
        Figure size in inches.

    Returns
    -------
    matplotlib.axes.Axes
        Axes object containing the plot.

    Raises
    ------
    ValueError
        If `importances` is not a pandas Series, is empty, or `top_n` is invalid.
    """
    if not isinstance(importances, pd.Series):
        raise ValueError("importances must be a pandas Series.")
    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")
    if importances.empty:
        raise ValueError("importances is empty.")

    top_n = min(top_n, len(importances))
    top = importances.head(top_n).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(top.index, top.values)
    ax.set_xlabel("Feature importance")
    ax.set_title(title)

    plt.tight_layout()
    return ax


# ---------------------------------------------------------------------
# Mapping classification and side-by-side comparison
# ---------------------------------------------------------------------

def classify_for_mapping(
    gdf,
    col,
    scheme="quantile",
    k=10,
    label_fmt="{lo:.2f}–{hi:.2f}",
    min_unique_to_bin=10,
):
    """
    Prepare a column for mapping.

    Numeric variables with more than `min_unique_to_bin` unique values
    are binned into ordered classes. Other variables are treated as
    categorical as-is.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame.
    col : str
        Column to prepare for mapping.
    scheme : {"quantile", "equal", "natural"}, optional
        Classification scheme for numeric variables.
    k : int, optional
        Number of classes for numeric variables.
    label_fmt : str, optional
        Format string used for class labels.
    min_unique_to_bin : int, optional
        Only bin numeric variables when the number of unique values
        exceeds this threshold.

    Returns
    -------
    tuple
        A tuple containing:
        - GeoDataFrame with mapped column
        - name of mapped column
        - boolean indicating categorical treatment

    Raises
    ------
    ValueError
        If inputs are invalid.
    ImportError
        If natural breaks are requested but `mapclassify` is not installed.
    """
    if col not in gdf.columns:
        raise ValueError(f"'{col}' not found in GeoDataFrame.")
    if scheme not in {"quantile", "equal", "natural"}:
        raise ValueError("scheme must be one of: 'quantile', 'equal', 'natural'.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer.")
    if not isinstance(min_unique_to_bin, int) or min_unique_to_bin < 0:
        raise ValueError("min_unique_to_bin must be a non-negative integer.")

    s = gdf[col]
    gdf_out = gdf.copy()

    # Treat non-numeric columns as categorical without binning
    if not pd.api.types.is_numeric_dtype(s):
        return gdf_out, col, True

    n_unique = s.dropna().nunique()
    if n_unique <= min_unique_to_bin:
        return gdf_out, col, True

    s_nonnull = s.dropna()
    if s_nonnull.empty:
        return gdf_out, col, True

    # Build class intervals using the requested scheme
    if scheme == "quantile":
        bins = pd.qcut(s_nonnull, q=k, duplicates="drop")
        cats = bins.cat.categories

    elif scheme == "equal":
        bins = pd.cut(s_nonnull, bins=k, duplicates="drop")
        cats = bins.cat.categories

    else:
        try:
            import mapclassify as mc
        except ImportError as e:
            raise ImportError(
                "Natural breaks requires `mapclassify`. Install it with: pip install mapclassify"
            ) from e

        classifier = mc.NaturalBreaks(s_nonnull.to_numpy(), k=k)
        yb = pd.Series(classifier.yb, index=s_nonnull.index)

        edges = np.r_[float(s_nonnull.min()), classifier.bins]
        intervals = [
            pd.Interval(edges[i], edges[i + 1], closed="right")
            for i in range(len(edges) - 1)
        ]
        cats = pd.Index(intervals)

        bins = pd.Categorical.from_codes(
            yb.to_numpy(),
            categories=cats,
            ordered=True,
        )
        bins = pd.Series(bins, index=s_nonnull.index)

    def _label_interval(iv):
        return label_fmt.format(lo=iv.left, hi=iv.right)

    labels = [_label_interval(iv) for iv in cats]

    mapped = pd.Series(pd.NA, index=s.index, dtype="object")

    if scheme in {"quantile", "equal"}:
        codes = bins.cat.codes.to_numpy()
    else:
        codes = pd.Categorical(bins, categories=cats, ordered=True).codes

    mapped.loc[s_nonnull.index] = [labels[c] if c >= 0 else pd.NA for c in codes]

    mapped_col = f"{col}__{scheme}_k{k}"
    gdf_out[mapped_col] = pd.Categorical(mapped, categories=labels, ordered=True)

    return gdf_out, mapped_col, True


def show_two_maps_side_by_side(
    gdf,
    left_var,
    right_var,
    tooltip_cols=(),
    scheme="quantile",
    k=10,
    min_unique_to_bin=10,
    cmap_left="YlOrRd_r",
    cmap_right="viridis",
    pois=None,
    zoom_start=10,
):
    """
    Display two Folium maps side by side.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame.
    left_var : str
        Variable to display on the left map.
    right_var : str
        Variable to display on the right map.
    tooltip_cols : tuple of str, optional
        Columns to display in map tooltips.
    scheme : {"quantile", "equal", "natural"}, optional
        Classification scheme for numeric variables.
    k : int, optional
        Number of classes for numeric variables.
    min_unique_to_bin : int, optional
        Only bin numeric variables when the number of unique values exceeds
        this threshold.
    cmap_left : str, optional
        Colour map for the left map.
    cmap_right : str, optional
        Colour map for the right map.
    pois : str or None, optional
        Optional reference points text.
    zoom_start : int, optional
        Initial zoom level before fit bounds are applied.

    Returns
    -------
    None
        Displays two maps side by side in the notebook.
    """
    if left_var not in gdf.columns:
        raise ValueError(f"'{left_var}' not found in GeoDataFrame.")
    if right_var not in gdf.columns:
        raise ValueError(f"'{right_var}' not found in GeoDataFrame.")

    # Prepare both variables for mapping
    g_left, left_mapped, _ = classify_for_mapping(
        gdf,
        left_var,
        scheme=scheme,
        k=k,
        min_unique_to_bin=min_unique_to_bin,
    )

    g_right, right_mapped, _ = classify_for_mapping(
        gdf,
        right_var,
        scheme=scheme,
        k=k,
        min_unique_to_bin=min_unique_to_bin,
    )

    # Build the two interactive maps
    m_left = make_webmap_general(
        focus_gdf=g_left,
        focus_col=left_mapped,
        focus_name=left_var,
        focus_tooltip_cols=tooltip_cols,
        focus_categorical=True,
        focus_legend=True,
        focus_cmap=cmap_left,
        pois=pois,
        zoom_start=zoom_start,
    )

    m_right = make_webmap_general(
        focus_gdf=g_right,
        focus_col=right_mapped,
        focus_name=right_var,
        focus_tooltip_cols=tooltip_cols,
        focus_categorical=True,
        focus_legend=True,
        focus_cmap=cmap_right,
        pois=pois,
        zoom_start=zoom_start,
    )

    # Display maps in a simple two-column layout
    html = f"""
    <div style="display:flex; gap:10px;">
      <div style="width:50%;">{m_left._repr_html_()}</div>
      <div style="width:50%;">{m_right._repr_html_()}</div>
    </div>
    """
    display(HTML(html))