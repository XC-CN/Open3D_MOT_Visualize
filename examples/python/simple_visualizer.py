#!/usr/bin/env python3
"""
Simple MCTrack Visualizer - Quick test version
"""

import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import os
import sys

try:
    from nuscenes.nuscenes import NuScenes
    NUSCENES_AVAILABLE = True
except ImportError:
    print("Warning: nuscenes-devkit not available")
    NUSCENES_AVAILABLE = False


class SimpleVisualizer:
    def __init__(self):
        self.nusc = None
        self.scene_token = None
        self.sample_tokens = []
        self.current_frame = 0
        
        # Initialize GUI
        gui.Application.instance.initialize()
        self.window = gui.Application.instance.create_window("nuScenes Simple Viewer", 1200, 800)
        
        # 3D Scene
        self.scene_widget = gui.SceneWidget()
        self.scene_widget.scene = rendering.Open3DScene(self.window.renderer)
        
        # Control Panel
        em = self.window.theme.font_size
        self.control_panel = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))
        
        # Load button
        self.load_button = gui.Button("Load nuScenes Data")
        self.load_button.set_on_clicked(self._on_load_data)
        self.control_panel.add_child(self.load_button)
        
        # Timeline
        timeline_layout = gui.Horiz(0.25 * em)
        timeline_layout.add_child(gui.Label("Frame:"))
        
        self.timeline_slider = gui.Slider(gui.Slider.INT)
        self.timeline_slider.set_limits(0, 100)
        self.timeline_slider.set_on_value_changed(self._on_frame_changed)
        timeline_layout.add_child(self.timeline_slider)
        self.control_panel.add_child(timeline_layout)
        
        # Control buttons
        button_layout = gui.Horiz(0.25 * em)
        
        self.prev_button = gui.Button("Previous")
        self.prev_button.set_on_clicked(self._on_prev)
        button_layout.add_child(self.prev_button)
        
        self.next_button = gui.Button("Next")
        self.next_button.set_on_clicked(self._on_next)
        button_layout.add_child(self.next_button)
        
        self.control_panel.add_child(button_layout)
        
        # Info text
        self.info_text = gui.Label("Load nuScenes data to begin")
        self.control_panel.add_child(self.info_text)
        
        # Layout
        self.window.set_on_layout(self._on_layout)
        self.window.add_child(self.scene_widget)
        self.window.add_child(self.control_panel)
        
        # Apply settings
        self.scene_widget.scene.set_background([0.1, 0.1, 0.1, 1.0])
        self.scene_widget.scene.show_axes(True)\n        \n    def _on_layout(self, layout_context):\n        r = self.window.content_rect\n        panel_width = 15 * layout_context.theme.font_size\n        \n        self.scene_widget.frame = gui.Rect(r.x, r.y, r.width - panel_width, r.height)\n        self.control_panel.frame = gui.Rect(r.x + r.width - panel_width, r.y, panel_width, r.height)\n        \n    def _on_load_data(self):\n        if not NUSCENES_AVAILABLE:\n            self._show_message("Error", "nuscenes-devkit not installed")\n            return\n            \n        # Try to load nuScenes\n        data_path = "D:/OneDrive/NUS/ME5400/MCTrack/data/nuScenes/datasets"\n        if not os.path.exists(data_path):\n            self._show_message("Error", f"Data path not found: {data_path}")\n            return\n            \n        try:\n            # Try different versions\n            for version in ['v1.0-trainval', 'v1.0-mini', 'v1.0-test']:\n                try:\n                    self.nusc = NuScenes(version=version, dataroot=data_path, verbose=True)\n                    print(f"Loaded {version}")\n                    break\n                except:\n                    continue\n                    \n            if self.nusc is None:\n                raise Exception("Cannot load any nuScenes version")\n                \n            # Load first scene\n            if len(self.nusc.scene) > 0:\n                self.scene_token = self.nusc.scene[0]['token']\n                self._load_scene_data()\n                self._show_frame(0)\n                self._show_message("Success", f"Loaded {self.nusc.version} with {len(self.sample_tokens)} frames")\n            else:\n                raise Exception("No scenes found")\n                \n        except Exception as e:\n            self._show_message("Error", f"Failed to load nuScenes: {str(e)}")\n            \n    def _load_scene_data(self):\n        scene = self.nusc.get('scene', self.scene_token)\n        \n        # Get all sample tokens\n        self.sample_tokens = []\n        sample_token = scene['first_sample_token']\n        while sample_token:\n            self.sample_tokens.append(sample_token)\n            sample = self.nusc.get('sample', sample_token)\n            sample_token = sample['next']\n            \n        # Update slider\n        if len(self.sample_tokens) > 0:\n            self.timeline_slider.set_limits(0, len(self.sample_tokens) - 1)\n            self.timeline_slider.int_value = 0\n            \n    def _show_frame(self, frame_id):\n        if frame_id >= len(self.sample_tokens) or frame_id < 0:\n            return\n            \n        # Clear previous geometry\n        self.scene_widget.scene.clear_geometry()\n        \n        sample_token = self.sample_tokens[frame_id]\n        sample = self.nusc.get('sample', sample_token)\n        \n        # Load point cloud\n        self._load_point_cloud(sample)\n        \n        # Update info\n        self.info_text.text = f"Frame: {frame_id + 1}/{len(self.sample_tokens)}"\n        self.current_frame = frame_id\n        \n        # Setup camera on first frame\n        if frame_id == 0:\n            bounds = o3d.geometry.AxisAlignedBoundingBox([-50, -50, -5], [50, 50, 5])\n            self.scene_widget.setup_camera(60, bounds, [0, 0, 0])\n            \n    def _load_point_cloud(self, sample):\n        try:\n            lidar_token = sample['data']['LIDAR_TOP']\n            lidar_data = self.nusc.get('sample_data', lidar_token)\n            \n            # Load point cloud file\n            pc_path = os.path.join(self.nusc.dataroot, lidar_data['filename'])\n            if os.path.exists(pc_path) and pc_path.endswith('.pcd.bin'):\n                # Read nuScenes point cloud format\n                points_data = np.fromfile(pc_path, dtype=np.float32).reshape(-1, 5)\n                points = points_data[:, :3]  # x, y, z\n                \n                # Create point cloud\n                pcd = o3d.geometry.PointCloud()\n                pcd.points = o3d.utility.Vector3dVector(points)\n                \n                # Color by intensity\n                if points_data.shape[1] >= 4:\n                    intensities = points_data[:, 3]\n                    intensities_norm = (intensities - intensities.min()) / (intensities.max() - intensities.min() + 1e-8)\n                    colors = np.zeros((len(points), 3))\n                    colors[:, 0] = intensities_norm * 0.8\n                    colors[:, 1] = intensities_norm * 0.6\n                    colors[:, 2] = intensities_norm * 0.4\n                    pcd.colors = o3d.utility.Vector3dVector(colors)\n                else:\n                    pcd.paint_uniform_color([0.7, 0.7, 0.7])\n                    \n                # Add to scene\n                material = rendering.MaterialRecord()\n                material.point_size = 2.0\n                material.shader = "unlitPoints"\n                \n                self.scene_widget.scene.add_geometry("point_cloud", pcd, material)\n                print(f"Loaded {len(points)} points")\n            else:\n                print(f"Point cloud file not found: {pc_path}")\n                \n        except Exception as e:\n            print(f"Error loading point cloud: {str(e)}")\n            # Create test point cloud\n            test_points = np.random.rand(1000, 3) * 50 - 25\n            pcd = o3d.geometry.PointCloud()\n            pcd.points = o3d.utility.Vector3dVector(test_points)\n            pcd.paint_uniform_color([0.5, 0.5, 0.5])\n            \n            material = rendering.MaterialRecord()\n            material.point_size = 2.0\n            material.shader = "unlitPoints"\n            \n            self.scene_widget.scene.add_geometry("test_cloud", pcd, material)\n            \n    def _on_frame_changed(self, value):\n        frame_id = int(value)\n        if frame_id != self.current_frame:\n            self._show_frame(frame_id)\n            \n    def _on_prev(self):\n        if self.current_frame > 0:\n            new_frame = self.current_frame - 1\n            self.timeline_slider.int_value = new_frame\n            self._show_frame(new_frame)\n            \n    def _on_next(self):\n        if self.current_frame < len(self.sample_tokens) - 1:\n            new_frame = self.current_frame + 1\n            self.timeline_slider.int_value = new_frame\n            self._show_frame(new_frame)\n            \n    def _show_message(self, title, message):\n        dlg = gui.Dialog(title)\n        em = self.window.theme.font_size\n        \n        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))\n        dlg_layout.add_child(gui.Label(message))\n        \n        ok_button = gui.Button("OK")\n        ok_button.set_on_clicked(lambda: self.window.close_dialog())\n        \n        h = gui.Horiz()\n        h.add_stretch()\n        h.add_child(ok_button)\n        h.add_stretch()\n        dlg_layout.add_child(h)\n        \n        dlg.add_child(dlg_layout)\n        self.window.show_dialog(dlg)\n        \n    def run(self):\n        gui.Application.instance.run()


def main():\n    print("Simple nuScenes Visualizer")\n    print("=" * 30)\n    \n    visualizer = SimpleVisualizer()\n    visualizer.run()\n\n\nif __name__ == "__main__":\n    main()