# Import necessary libraries
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import geopandas as gpd
from shapely.geometry import box
import pandas as pd
import numpy as np
import os
import contextily as cx


# Function to calculate image size
def calculate_image_size(fig, dpi):
    return (int(fig.get_figwidth() * dpi), int(fig.get_figheight() * dpi))

# Function to add a north arrow to the map
def add_north_arrow(ax, location=(0.05, 0.95), size=0.05):
    x, y = location
    # Create an arrow patch
    arrow = patches.Arrow(x, y-size, 0, size, width=size/2, 
                          transform=ax.transAxes, fc='black', ec='black')
    ax.add_patch(arrow)
    # Add 'N' label
    ax.text(x, y+0.01, 'N', transform=ax.transAxes,
            ha='center', va='bottom', fontweight='bold', fontsize=9)

# Function to add a scale bar to the map
def add_scaled_bar(ax, length, location=(0.95, 0.05), linewidth=3):
    x, y = location
    # Draw the scale bar
    ax.plot([x, x - length], [y, y], color='k', linewidth=linewidth, transform=ax.transAxes)
    ax.plot([x - length/4, x - length/2], [y, y], color='w', linewidth=linewidth, transform=ax.transAxes)
    ax.plot([x - 3*length/4, x - length], [y, y], color='w', linewidth=linewidth, transform=ax.transAxes)
    # Add text label
    ax.text(x - length/2, y - 0.01, f'{int(length*map_width_meters)} m', ha='center', va='top', transform=ax.transAxes, fontsize=8)

# Load the project area shapefile
project_area_path = r"inset your path here"
project_area = gpd.read_file(project_area_path)

# Ensure project area is in UTM Zone 16
if project_area.crs != 'EPSG:32616':
    project_area = project_area.to_crs('EPSG:32616')

# Get the bounds of the project area
minx, miny, maxx, maxy = project_area.total_bounds

# Calculate the center of the project area
center_x, center_y = (minx + maxx) / 2, (miny + maxy) / 2

# Calculate the dimensions for 1:10000 scale
scale = 10000
inches_to_meters = 0.0254
map_width_meters = 24 * inches_to_meters * scale  # Assuming 24 inches wide map
map_height_meters = 36 * inches_to_meters * scale  # Assuming 36 inches high map

# Calculate new bounds
new_minx = center_x - map_width_meters / 2
new_maxx = center_x + map_width_meters / 2
new_miny = center_y - map_height_meters / 2
new_maxy = center_y + map_height_meters / 2

# Create a bounding box for clipping
clip_box = box(new_minx, new_miny, new_maxx, new_maxy)

# Load and clip the geology shapefile
geology_path = r"insert your path here"
geology = gpd.read_file(geology_path)

# Ensure geology is in UTM Zone 16
if geology.crs != 'EPSG:32616':
    geology = geology.to_crs('EPSG:32616')

# Perform the clip operation
geology_clipped = gpd.clip(geology, clip_box)

# Check if the clipped geology shapefile is empty
if geology_clipped.empty:
    print("Warning: The clipped geology shapefile is empty. There might be no overlap between the geology data and the project area.")
    exit()

# Simplify the geometry to reduce complexity
geology_clipped['geometry'] = geology_clipped.geometry.simplify(tolerance=100)

# Save the clipped geology shapefile
geology_clipped.to_file(r"insert your path here")

# Create a new figure
fig, ax = plt.subplots(figsize=(24, 36), dpi=100)

# Create color map for geology units
unique_units = geology_clipped['UNIT_NAME'].unique()
colors = plt.cm.get_cmap('tab20')(np.linspace(0, 1, len(unique_units)))
color_dict = dict(zip(unique_units, colors))

# Plot geology
for unit, data in geology_clipped.groupby('UNIT_NAME'):
    color = color_dict[unit]
    data.plot(ax=ax, color=color, edgecolor='black', linewidth=0.5, alpha=0.7)

# Plot project area
project_area.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)

# Add OpenStreetMap basemap
project_area_wgs84 = project_area.to_crs(epsg=4326)
cx.add_basemap(ax, crs=project_area.crs.to_string(), source=cx.providers.OpenStreetMap.Mapnik)

# Add scale bar
add_scaled_bar(ax, 0.2)

# Add north arrow
add_north_arrow(ax)

# Set map extent
ax.set_xlim(new_minx, new_maxx)
ax.set_ylim(new_miny, new_maxy)

# Create legend with Project Area
handles = [Line2D([0], [0], color='red', lw=2, linestyle='-', label='Project Area')]
labels = ['Project Area']

# Add geology types to legend
handles.extend([patches.Patch(color=color, alpha=0.7, label=unit) for unit, color in color_dict.items()])
labels.extend(unique_units)

# Create the legend layout 
legend = ax.legend(handles, labels, title='Legend\nGeology type = UNIT_NAME', loc='lower left', fontsize=9, 
                   bbox_to_anchor=(0.02, 0.02), ncol=1, frameon=True, fancybox=True, shadow=True)
legend.get_frame().set_facecolor('white')
legend.get_frame().set_edgecolor('black')
legend.get_title().set_fontsize(10)

# Remove axis labels
ax.set_axis_off()

# Add title
fig.suptitle('Geological Map of Project Area', fontsize=12, y=0.98)

# Check image size and resize if necessary
img_width, img_height = calculate_image_size(fig, 100)
max_size = 2**16 - 1

if img_width > max_size or img_height > max_size:
    scale_factor = min(max_size / img_width, max_size / img_height)
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)
    print(f"Warning: Image size too large. Resizing from {img_width}x{img_height} to {new_width}x{new_height}")
    fig.set_size_inches(new_width / 100, new_height / 100)

# Create output folder if it doesn't exist
output_folder = r"insert your output folder"
os.makedirs(output_folder, exist_ok=True)

# Save the figure
output_file = os.path.join(output_folder, 'geological_map_project_area.png')
plt.savefig(output_file, dpi=100, bbox_inches='tight')

print(f"Map has been created and saved as '{output_file}'")
print("Yay! Your map is in the folder!")

# Display the map
plt.show()