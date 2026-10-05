import math
import time

class Vec3:
    __slots__ = ("x", "y", "z")
    def __init__(self, x: float, y: float, z: float):
        self.x, self.y, self.z = x, y, z

    def __add__(self, o):
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o):
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s):
        return Vec3(self.x * s, self.y * s, self.z * s)

    def dot(self, o):
        return self.x * o.x + self.y * o.y + self.z * o.z

    def norm(self):
        m = math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
        return Vec3(self.x / m, self.y / m, self.z / m) if m > 0.0 else self

SPHERES = [
    (Vec3(0.0, -1.0, -3.0), 1.0),
    (Vec3(2.0, 0.0, -4.0), 1.0),
    (Vec3(-2.0, 0.0, -4.0), 1.0),
    (Vec3(1.5, 1.5, -5.0), 0.8),
    (Vec3(-1.5, 1.5, -5.0), 0.8),
    (Vec3(0.0, 2.5, -6.0), 1.2),
    (Vec3(0.0, -101.0, -5.0), 100.0),
]
LIGHT_DIR = Vec3(0.5, 1.0, -0.5).norm()

def intersect_sphere(center, radius, ray_origin, ray_dir):
    oc = ray_origin - center
    b = 2.0 * ray_dir.dot(oc)
    c = oc.dot(oc) - radius * radius
    disc = b * b - 4.0 * c
    if disc < 0.0:
        return -1.0
    return (-b - math.sqrt(disc)) / 2.0

def trace_ray(ray_origin, ray_dir):
    closest_t = 1e9
    hit_sphere = None
    for center, radius in SPHERES:
        t = intersect_sphere(center, radius, ray_origin, ray_dir)
        if 0.001 < t < closest_t:
            closest_t = t
            hit_sphere = center
    if hit_sphere is None:
        return 0.1
    hit_point = ray_origin + ray_dir * closest_t
    normal = (hit_point - hit_sphere).norm()
    diffuse = max(0.0, normal.dot(LIGHT_DIR))
    return 0.2 + 0.8 * diffuse

def render_row(y, width, height):
    row_sum = 0.0
    cam = Vec3(0.0, 0.0, 0.0)
    for x in range(width):
        u = (x - width / 2.0) / width
        v = (y - height / 2.0) / height
        ray_dir = Vec3(u, -v, -1.0).norm()
        row_sum += trace_ray(cam, ray_dir)
    return row_sum

def main():
    WIDTH, HEIGHT = 1000, 1000
    t0 = time.perf_counter()
    total = 0.0
    for y in range(HEIGHT):
        total += render_row(y, WIDTH, HEIGHT)
    elapsed = time.perf_counter() - t0
    print(f"Elapsed: {elapsed:.3f} s (Radiance: {total:.2f})")
    return elapsed

if __name__ == "__main__":
    main()
