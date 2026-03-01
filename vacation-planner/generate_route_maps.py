#!/usr/bin/env python3
"""Generate route maps for the vacation presentation."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUTPUT_DIR = "/Users/robpugh/Vibe/vacation-photos"

# Dark navy background matching the presentation
BG_COLOR = '#1a1a2e'
LAND_COLOR = '#2a2a4a'
LAND_EDGE = '#3a3a5a'
OCEAN_COLOR = BG_COLOR

# City coordinates (lon, lat)
CITIES = {
    "Santiago":       (-70.65, -33.45),
    "São Paulo":      (-46.63, -23.55),
    "Cuiabá":         (-56.10, -15.60),
    "Pantanal":       (-57.00, -17.50),
    "Bonito":         (-56.48, -21.13),
    "Campo Grande":   (-54.62, -20.47),
    "Rio de Janeiro": (-43.17, -22.91),
    "Paraty":         (-44.71, -23.22),
    "Ilha Grande":    (-44.23, -23.15),
    "Porto Seguro":   (-39.06, -16.45),
    "Trancoso":       (-39.10, -16.59),
    "Praia do Espelho": (-39.12, -16.78),
    "Arraial d'Ajuda": (-39.07, -16.48),
    "Salvador":        (-38.51, -12.97),
    "Morro de São Paulo": (-38.91, -13.38),
    "Boipeba":         (-38.93, -13.58),
}

# South America coastline outline (lon, lat) — rough but recognizable
SA_COAST = [
    (-77.0, 8.5), (-75.5, 6.0), (-77.5, 4.0), (-79.5, 1.5), (-80.0, -1.0),
    (-81.0, -4.5), (-79.5, -7.0), (-77.0, -10.0), (-75.5, -14.0), (-73.0, -16.0),
    (-70.5, -18.0), (-70.0, -20.0), (-69.5, -22.5), (-70.5, -27.0), (-71.5, -33.0),
    (-73.0, -37.0), (-73.5, -42.0), (-75.0, -46.0), (-74.0, -49.0), (-72.0, -52.0),
    (-69.0, -54.5), (-65.0, -55.0), (-64.0, -53.0), (-65.5, -50.0), (-67.0, -46.0),
    (-65.5, -42.0), (-63.0, -39.0), (-59.0, -37.5), (-56.5, -36.0), (-54.5, -34.0),
    (-53.0, -33.0), (-52.0, -32.0), (-50.0, -29.0), (-48.5, -27.0), (-48.0, -25.5),
    (-46.5, -24.0), (-44.0, -23.0), (-41.0, -22.5), (-40.0, -20.5), (-39.0, -17.0),
    (-38.5, -13.0), (-38.0, -10.0), (-35.5, -7.0), (-35.0, -5.5), (-36.5, -4.5),
    (-38.0, -3.5), (-41.0, -2.5), (-44.0, -2.0), (-46.5, -1.5), (-48.5, -1.5),
    (-50.0, 0.0), (-52.0, 2.0), (-55.0, 5.5), (-58.0, 7.0), (-62.0, 10.5),
    (-67.0, 11.0), (-72.0, 12.0), (-75.0, 11.0), (-77.0, 8.5),
]

# Tighter extent: shows Santiago but crops unnecessary west coast / Patagonia
DEFAULT_EXTENT = (-73, -34, -35, 0)


def draw_flight_arc(ax, start, end, color, lw=2.5):
    """Draw a curved flight path between two points."""
    x0, y0 = start
    x1, y1 = end
    mid_x = (x0 + x1) / 2
    mid_y = (y0 + y1) / 2
    dist = np.sqrt((x1-x0)**2 + (y1-y0)**2)
    dx, dy = x1-x0, y1-y0
    nx, ny = -dy/dist, dx/dist
    ctrl_x = mid_x + nx * dist * 0.15
    ctrl_y = mid_y + ny * dist * 0.15

    t = np.linspace(0, 1, 80)
    xs = (1-t)**2 * x0 + 2*(1-t)*t * ctrl_x + t**2 * x1
    ys = (1-t)**2 * y0 + 2*(1-t)*t * ctrl_y + t**2 * y1

    ax.plot(xs, ys, color=color, linewidth=lw, linestyle='--', alpha=0.8, zorder=5)
    ax.annotate('✈', xy=(ctrl_x, ctrl_y), fontsize=14, color=color,
                ha='center', va='center', zorder=6)


def draw_ground_route(ax, points, color, lw=2.5):
    """Draw a solid ground route through multiple points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle='round', zorder=5)


def draw_numbered_marker(ax, pos, number, color, marker_size=8):
    """Draw a numbered circle marker."""
    ax.plot(pos[0], pos[1], 'o', color=color, markersize=marker_size,
            markeredgecolor='white', markeredgewidth=0.8, zorder=7)
    ax.annotate(str(number), xy=pos, fontsize=7, color='white',
                ha='center', va='center', weight='bold', zorder=8)


def draw_city_marker(ax, pos, name, color, fontsize=10, offset=(0.5, 0.5),
                     bold=False, marker_size=6):
    """Draw a city dot and label."""
    ax.plot(pos[0], pos[1], 'o', color=color, markersize=marker_size,
            markeredgecolor='white', markeredgewidth=0.8, zorder=7)
    weight = 'bold' if bold else 'normal'
    ax.annotate(name, xy=pos, xytext=(pos[0]+offset[0], pos[1]+offset[1]),
                fontsize=fontsize, color='white', weight=weight,
                zorder=8, ha='left', va='center',
                arrowprops=dict(arrowstyle='-', color='#666666', lw=0.5)
                if abs(offset[0]) > 1.5 or abs(offset[1]) > 1.5 else None)


def add_legend(ax, items, color, x=0.02, y=0.02):
    """Add a numbered legend box in a corner.
    items = [(number, "City Name"), ...]
    """
    legend_text = "\n".join(f"  {n}  {name}" for n, name in items)
    ax.text(x, y, legend_text, transform=ax.transAxes,
            fontsize=10, color='white', family='monospace',
            verticalalignment='bottom', weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#0d0d1a',
                      edgecolor=color, alpha=0.9),
            zorder=10)


def setup_map(ax, extent=None):
    """Set up the base map with South America outline."""
    ax.set_facecolor(OCEAN_COLOR)
    coast_x = [p[0] for p in SA_COAST]
    coast_y = [p[1] for p in SA_COAST]
    ax.fill(coast_x, coast_y, color=LAND_COLOR, edgecolor=LAND_EDGE,
            linewidth=0.8, zorder=1)
    if extent:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
    ax.set_aspect('equal')
    ax.axis('off')


def save_map(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', pad_inches=0.1,
                facecolor=BG_COLOR, edgecolor='none')
    plt.close(fig)
    print(f"  Saved {name}")
    return path


def make_pantanal_map():
    """Pantanal + Bonito route map."""
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG_COLOR)
    setup_map(ax, extent=DEFAULT_EXTENT)
    color = '#2ecc71'

    # Flights out: Santiago > São Paulo > Cuiabá
    draw_flight_arc(ax, CITIES["Santiago"], CITIES["São Paulo"], color)
    draw_flight_arc(ax, CITIES["São Paulo"], CITIES["Cuiabá"], color)

    # Ground: Cuiabá > Pantanal > Bonito > Campo Grande
    draw_ground_route(ax, [
        CITIES["Cuiabá"], CITIES["Pantanal"], CITIES["Bonito"], CITIES["Campo Grande"]
    ], color)

    # Return: Campo Grande > São Paulo
    draw_flight_arc(ax, CITIES["Campo Grande"], CITIES["São Paulo"], color, lw=1.5)

    # City markers — all spread out enough for direct labels
    draw_city_marker(ax, CITIES["Santiago"], "Santiago", color, fontsize=11,
                     offset=(-1.5, -1.5), bold=True)
    draw_city_marker(ax, CITIES["São Paulo"], "São Paulo", color, fontsize=9,
                     offset=(0.5, -1.2))
    draw_city_marker(ax, CITIES["Cuiabá"], "Cuiabá", color, fontsize=10,
                     offset=(0.5, 0.8), bold=True)
    draw_city_marker(ax, CITIES["Pantanal"], "Pantanal", color, fontsize=11,
                     offset=(-3, -1.2), bold=True, marker_size=8)
    draw_city_marker(ax, CITIES["Bonito"], "Bonito", color, fontsize=10,
                     offset=(-2.5, -1), bold=True)
    draw_city_marker(ax, CITIES["Campo Grande"], "Campo Grande", color, fontsize=9,
                     offset=(0.5, -1))

    save_map(fig, "map_pantanal.jpg")


def make_bahia_map():
    """Salvador + Morro de São Paulo + Boipeba route map — numbered legend for close cities."""
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG_COLOR)
    setup_map(ax, extent=DEFAULT_EXTENT)
    color = '#00b8d4'

    # Flight out: Santiago > São Paulo > Salvador
    draw_flight_arc(ax, CITIES["Santiago"], CITIES["São Paulo"], color)
    draw_flight_arc(ax, CITIES["São Paulo"], CITIES["Salvador"], color)

    # Ground/boat: Salvador > Morro > Boipeba > back to Salvador
    draw_ground_route(ax, [CITIES["Salvador"], CITIES["Morro de São Paulo"]], color)
    ax.plot([CITIES["Morro de São Paulo"][0], CITIES["Boipeba"][0]],
            [CITIES["Morro de São Paulo"][1], CITIES["Boipeba"][1]],
            color=color, linewidth=2, linestyle=':', zorder=5)
    draw_ground_route(ax, [CITIES["Boipeba"], CITIES["Salvador"]], color, lw=1.5)

    # Santiago + São Paulo: direct labels (far from cluster)
    draw_city_marker(ax, CITIES["Santiago"], "Santiago", color, fontsize=11,
                     offset=(-1.5, -1.5), bold=True)
    draw_city_marker(ax, CITIES["São Paulo"], "São Paulo", color, fontsize=9,
                     offset=(0.5, -1.2))

    # NE Brazil cluster: numbered markers
    draw_numbered_marker(ax, CITIES["Salvador"], 1, color, marker_size=10)
    draw_numbered_marker(ax, CITIES["Morro de São Paulo"], 2, color, marker_size=9)
    draw_numbered_marker(ax, CITIES["Boipeba"], 3, color, marker_size=9)

    add_legend(ax, [
        (1, "Salvador"),
        (2, "Morro de São Paulo"),
        (3, "Boipeba"),
    ], color, x=0.68, y=0.02)

    save_map(fig, "map_bahia.jpg")


def make_rio_map():
    """Rio + Paraty + Ilha Grande route map — numbered legend for coastal cluster."""
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG_COLOR)
    setup_map(ax, extent=DEFAULT_EXTENT)
    color = '#ffd700'

    # Nonstop flight: Santiago > Rio
    draw_flight_arc(ax, CITIES["Santiago"], CITIES["Rio de Janeiro"], color)

    # NONSTOP label
    ax.text(-58, -20, "NONSTOP\n4 hours!", fontsize=13, color=color,
            ha='center', va='center', weight='bold', zorder=8,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BG_COLOR, edgecolor=color, alpha=0.9))

    # Ground: Rio > Paraty, boat to Ilha Grande, back to Rio
    draw_ground_route(ax, [CITIES["Rio de Janeiro"], CITIES["Paraty"]], color)
    ax.plot([CITIES["Paraty"][0], CITIES["Ilha Grande"][0]],
            [CITIES["Paraty"][1], CITIES["Ilha Grande"][1]],
            color=color, linewidth=2, linestyle=':', zorder=5)
    draw_ground_route(ax, [CITIES["Ilha Grande"], CITIES["Rio de Janeiro"]], color, lw=1.5)

    # Santiago: direct label
    draw_city_marker(ax, CITIES["Santiago"], "Santiago", color, fontsize=11,
                     offset=(-1.5, -1.5), bold=True)

    # Rio coast cluster: numbered markers
    draw_numbered_marker(ax, CITIES["Rio de Janeiro"], 1, color, marker_size=10)
    draw_numbered_marker(ax, CITIES["Paraty"], 2, color, marker_size=9)
    draw_numbered_marker(ax, CITIES["Ilha Grande"], 3, color, marker_size=9)

    add_legend(ax, [
        (1, "Rio de Janeiro"),
        (2, "Paraty"),
        (3, "Ilha Grande"),
    ], color, x=0.68, y=0.02)

    save_map(fig, "map_rio.jpg")


def make_trancoso_map():
    """Trancoso route map — simple, no inset."""
    fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG_COLOR)
    setup_map(ax, extent=DEFAULT_EXTENT)
    color = '#ff6348'

    # Flights: Santiago > São Paulo > Porto Seguro
    draw_flight_arc(ax, CITIES["Santiago"], CITIES["São Paulo"], color)
    draw_flight_arc(ax, CITIES["São Paulo"], CITIES["Porto Seguro"], color)

    # City markers
    draw_city_marker(ax, CITIES["Santiago"], "Santiago", color, fontsize=11,
                     offset=(-1.5, -1.5), bold=True)
    draw_city_marker(ax, CITIES["São Paulo"], "São Paulo", color, fontsize=9,
                     offset=(0.5, -1.2))

    # Trancoso area: numbered markers for cluster
    draw_numbered_marker(ax, CITIES["Porto Seguro"], 1, color, marker_size=9)
    draw_numbered_marker(ax, CITIES["Trancoso"], 2, color, marker_size=9)
    draw_numbered_marker(ax, CITIES["Praia do Espelho"], 3, color, marker_size=9)

    # Ground route in main map (they're close but visible as separate dots)
    draw_ground_route(ax, [CITIES["Porto Seguro"], CITIES["Trancoso"]], color, lw=2)
    ax.plot([CITIES["Trancoso"][0], CITIES["Praia do Espelho"][0]],
            [CITIES["Trancoso"][1], CITIES["Praia do Espelho"][1]],
            color=color, linewidth=2, linestyle=':', zorder=5)

    add_legend(ax, [
        (1, "Porto Seguro"),
        (2, "Trancoso"),
        (3, "Praia do Espelho"),
    ], color, x=0.68, y=0.02)

    save_map(fig, "map_trancoso.jpg")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating route maps...")
    make_pantanal_map()
    make_bahia_map()
    make_rio_map()
    make_trancoso_map()
    print("Done! Check vacation-photos/ for map_*.jpg")
