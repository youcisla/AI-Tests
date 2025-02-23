import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import Voronoi
from groq import Groq

def draw_dotted_line(draw, start, end, dot_radius, gap):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dist = math.hypot(dx, dy)
    steps = max(int(dist / gap), 1)
    for i in range(steps + 1):
        t = i / steps
        x = start[0] + t * dx
        y = start[1] + t * dy
        draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=(0, 0, 0))

def voronoi_finite_polygons_2d(vor, radius=None):
    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")
    new_regions = []
    new_vertices = vor.vertices.tolist()
    center = vor.points.mean(axis=0)
    if radius is None:
        radius = np.ptp(vor.points, axis=0).max() * 2
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]
        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)
            continue
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]
        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                continue
            t = vor.points[p2] - vor.points[p1]
            t = t / np.linalg.norm(t)
            n = np.array([-t[1], t[0]])
            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius
            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())
        new_regions.append(new_region)
    return new_regions, np.array(new_vertices)

def generate_preview(complexity=5, dimension="2D"):
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    num_points = int(10 + complexity * 3)
    points = np.random.rand(num_points, 2) * 200
    vor = Voronoi(points)
    regions, vertices = voronoi_finite_polygons_2d(vor)
    dot_radius = 1 if dimension == "2D" else 2
    gap = 4 if dimension == "2D" else 3
    for region in regions:
        polygon = [tuple(vertices[v]) for v in region]
        if len(polygon) > 2:
            for j in range(len(polygon)):
                start = polygon[j]
                end = polygon[(j + 1) % len(polygon)]
                draw_dotted_line(draw, start, end, dot_radius, gap)
    return img

def generate_shapes(complexity=5, num_shapes=50, output_dir="shapes", dimension="2D", progress_callback=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i in range(num_shapes):
        img = Image.new("RGB", (1000, 1000), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        num_points = int(20 + complexity * 10)
        points = np.random.rand(num_points, 2) * 1000
        vor = Voronoi(points)
        regions, vertices = voronoi_finite_polygons_2d(vor)
        dot_radius = 1 if dimension == "2D" else 2
        gap = 4 if dimension == "2D" else 3
        for region in regions:
            polygon = [tuple(vertices[v]) for v in region]
            if len(polygon) > 2:
                for j in range(len(polygon)):
                    start = polygon[j]
                    end = polygon[(j + 1) % len(polygon)]
                    draw_dotted_line(draw, start, end, dot_radius, gap)
        img.save(os.path.join(output_dir, f"shape_{i+1}.png"), "PNG")
        if progress_callback:
            progress_callback(i + 1, num_shapes)
