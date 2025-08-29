#!/usr/bin/env python3
"""
Demo nuScenes Viewer - Quick test for visualizing nuScenes scenes
"""

import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import os

try:
    from nuscenes.nuscenes import NuScenes
    NUSCENES_AVAILABLE = True
except ImportError:
    print("Warning: nuscenes-devkit not available")
    NUSCENES_AVAILABLE = False


class DemoViewer:
    def __init__(self):
        self.nusc = None
        self.scene_token = None
        self.sample_tokens = []
        self.current_frame = 0
        
        # Initialize GUI
        gui.Application.instance.initialize()
        self.window = gui.Application.instance.create_window("nuScenes Demo Viewer", 1200, 800)
        
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
        self.scene_widget.scene.show_axes(True)
        
    def _on_layout(self, layout_context):
        r = self.window.content_rect
        panel_width = 15 * layout_context.theme.font_size
        
        self.scene_widget.frame = gui.Rect(r.x, r.y, r.width - panel_width, r.height)
        self.control_panel.frame = gui.Rect(r.x + r.width - panel_width, r.y, panel_width, r.height)
        
    def _on_load_data(self):
        if not NUSCENES_AVAILABLE:
            self._show_message("Error", "nuscenes-devkit not installed")
            return
            
        # Try to load nuScenes
        data_path = "D:/OneDrive/NUS/ME5400/MCTrack/data/nuScenes/datasets"
        if not os.path.exists(data_path):
            self._show_message("Error", f"Data path not found: {data_path}")
            return
            
        try:
            # Try different versions
            for version in ['v1.0-trainval', 'v1.0-mini', 'v1.0-test']:
                try:
                    self.nusc = NuScenes(version=version, dataroot=data_path, verbose=True)
                    print(f"Loaded {version}")
                    break
                except:
                    continue
                    
            if self.nusc is None:
                raise Exception("Cannot load any nuScenes version")
                
            # Load first scene
            if len(self.nusc.scene) > 0:
                self.scene_token = self.nusc.scene[0]['token']
                self._load_scene_data()
                self._show_frame(0)
                self._show_message("Success", f"Loaded {self.nusc.version} with {len(self.sample_tokens)} frames")
            else:
                raise Exception("No scenes found")
                
        except Exception as e:
            self._show_message("Error", f"Failed to load nuScenes: {str(e)}")
            
    def _load_scene_data(self):
        scene = self.nusc.get('scene', self.scene_token)
        
        # Get all sample tokens
        self.sample_tokens = []
        sample_token = scene['first_sample_token']
        while sample_token:
            self.sample_tokens.append(sample_token)
            sample = self.nusc.get('sample', sample_token)
            sample_token = sample['next']
            
        # Update slider
        if len(self.sample_tokens) > 0:
            self.timeline_slider.set_limits(0, len(self.sample_tokens) - 1)
            self.timeline_slider.int_value = 0
            
    def _show_frame(self, frame_id):
        if frame_id >= len(self.sample_tokens) or frame_id < 0:
            return
            
        # Clear previous geometry
        self.scene_widget.scene.clear_geometry()
        
        sample_token = self.sample_tokens[frame_id]
        sample = self.nusc.get('sample', sample_token)
        
        # Load point cloud
        self._load_point_cloud(sample)
        
        # Update info
        self.info_text.text = f"Frame: {frame_id + 1}/{len(self.sample_tokens)}"
        self.current_frame = frame_id
        
        # Setup camera on first frame
        if frame_id == 0:
            bounds = o3d.geometry.AxisAlignedBoundingBox([-50, -50, -5], [50, 50, 5])
            self.scene_widget.setup_camera(60, bounds, [0, 0, 0])
            
    def _load_point_cloud(self, sample):
        try:
            lidar_token = sample['data']['LIDAR_TOP']
            lidar_data = self.nusc.get('sample_data', lidar_token)
            
            # Load point cloud file
            pc_path = os.path.join(self.nusc.dataroot, lidar_data['filename'])
            if os.path.exists(pc_path) and pc_path.endswith('.pcd.bin'):
                # Read nuScenes point cloud format
                points_data = np.fromfile(pc_path, dtype=np.float32).reshape(-1, 5)
                points = points_data[:, :3]  # x, y, z
                
                # Create point cloud
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(points)
                
                # Color by intensity
                if points_data.shape[1] >= 4:
                    intensities = points_data[:, 3]
                    intensities_norm = (intensities - intensities.min()) / (intensities.max() - intensities.min() + 1e-8)
                    colors = np.zeros((len(points), 3))
                    colors[:, 0] = intensities_norm * 0.8
                    colors[:, 1] = intensities_norm * 0.6
                    colors[:, 2] = intensities_norm * 0.4
                    pcd.colors = o3d.utility.Vector3dVector(colors)
                else:
                    pcd.paint_uniform_color([0.7, 0.7, 0.7])
                    
                # Add to scene
                material = rendering.MaterialRecord()
                material.point_size = 2.0
                material.shader = "unlitPoints"
                
                self.scene_widget.scene.add_geometry("point_cloud", pcd, material)
                print(f"Loaded {len(points)} points")
            else:
                print(f"Point cloud file not found: {pc_path}")
                
        except Exception as e:
            print(f"Error loading point cloud: {str(e)}")
            # Create test point cloud
            test_points = np.random.rand(1000, 3) * 50 - 25
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(test_points)
            pcd.paint_uniform_color([0.5, 0.5, 0.5])
            
            material = rendering.MaterialRecord()
            material.point_size = 2.0
            material.shader = "unlitPoints"
            
            self.scene_widget.scene.add_geometry("test_cloud", pcd, material)
            
    def _on_frame_changed(self, value):
        frame_id = int(value)
        if frame_id != self.current_frame:
            self._show_frame(frame_id)
            
    def _on_prev(self):
        if self.current_frame > 0:
            new_frame = self.current_frame - 1
            self.timeline_slider.int_value = new_frame
            self._show_frame(new_frame)
            
    def _on_next(self):
        if self.current_frame < len(self.sample_tokens) - 1:
            new_frame = self.current_frame + 1
            self.timeline_slider.int_value = new_frame
            self._show_frame(new_frame)
            
    def _show_message(self, title, message):
        dlg = gui.Dialog(title)
        em = self.window.theme.font_size
        
        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label(message))
        
        ok_button = gui.Button("OK")
        ok_button.set_on_clicked(lambda: self.window.close_dialog())
        
        h = gui.Horiz()
        h.add_stretch()
        h.add_child(ok_button)
        h.add_stretch()
        dlg_layout.add_child(h)
        
        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)
        
    def run(self):
        gui.Application.instance.run()


def main():
    print("Demo nuScenes Visualizer")
    print("=" * 30)
    
    viewer = DemoViewer()
    viewer.run()


if __name__ == "__main__":
    main()