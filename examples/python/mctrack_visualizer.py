#!/usr/bin/env python3
"""
MCTrack Visualizer - 基于Open3D GUI的多目标跟踪可视化工具
支持nuScenes数据集和MCTrack跟踪结果的同步可视化
"""

import json
import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import colorsys
import time

try:
    from nuscenes.nuscenes import NuScenes
    from nuscenes.utils.data_classes import Box
    from nuscenes.utils.geometry_utils import transform_matrix
    NUSCENES_AVAILABLE = True
except ImportError:
    print("Warning: nuscenes-devkit not available. Some features will be limited.")
    NUSCENES_AVAILABLE = False


class MCTrackSettings:
    """MCTrack可视化设置"""
    
    def __init__(self):
        # 显示设置
        self.show_point_cloud = True
        self.show_tracking_boxes = True
        self.show_trajectories = True
        self.show_ground_truth = False
        
        # 点云设置
        self.point_size = 2.0
        self.point_cloud_color = [0.5, 0.5, 0.5]
        
        # 跟踪框设置
        self.box_line_width = 2.0
        self.trajectory_length = 20  # 显示的历史轨迹长度
        
        # 播放控制
        self.auto_play = False
        self.play_speed = 1.0  # 播放速度倍数
        self.current_frame = 0
        self.total_frames = 0
        
        # 颜色设置
        self.use_track_id_colors = True
        self.color_palette = self._generate_color_palette(50)
        
    def _generate_color_palette(self, num_colors: int) -> List[List[float]]:
        """生成不同的颜色用于区分不同的跟踪ID"""
        colors = []
        for i in range(num_colors):
            hue = i / num_colors
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            colors.append(list(rgb))
        return colors


class MCTrackVisualizer:
    """MCTrack可视化工具主类"""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.settings = MCTrackSettings()
        
        # 数据存储
        self.nusc = None
        self.scene_token = None
        self.scene_data = None
        self.tracking_data = None
        self.sample_tokens = []
        
        # GUI组件
        self.window = None
        self.scene_widget = None
        self.timeline_slider = None
        self.play_button = None
        self.info_text = None
        
        # 状态
        self.is_playing = False
        self.last_play_time = 0
        
        # 几何对象缓存
        self.current_geometries = {}
        
        self._init_gui(width, height)
        
    def _init_gui(self, width: int, height: int):
        """初始化GUI界面"""
        gui.Application.instance.initialize()
        
        self.window = gui.Application.instance.create_window(
            "MCTrack Visualizer", width, height)
        
        # 主要的3D显示区域
        self.scene_widget = gui.SceneWidget()
        self.scene_widget.scene = rendering.Open3DScene(self.window.renderer)
        self.scene_widget.set_on_sun_direction_changed(self._on_sun_dir_changed)
        
        # 创建控制面板
        self._create_control_panel()
        
        # 设置布局
        self.window.set_on_layout(self._on_layout)
        self.window.add_child(self.scene_widget)
        self.window.add_child(self.control_panel)
        
        # 应用默认设置
        self._apply_visualization_settings()
        
    def _create_control_panel(self):
        """创建控制面板"""
        em = self.window.theme.font_size
        margin = 0.25 * em
        
        self.control_panel = gui.Vert(0, gui.Margins(margin, margin, margin, margin))
        
        # === 数据加载区域 ===
        file_section = gui.CollapsableVert("Data Loading", 0.25 * em, gui.Margins(em, 0, 0, 0))
        
        # nuScenes数据路径
        h1 = gui.Horiz(0.25 * em)
        h1.add_child(gui.Label("nuScenes Path:"))
        self.nuscenes_path_text = gui.TextEdit()
        self.nuscenes_path_text.text_value = "data/nuScenes/datasets"
        h1.add_child(self.nuscenes_path_text)
        
        self.load_nuscenes_button = gui.Button("Load Data")
        self.load_nuscenes_button.set_on_clicked(self._on_load_nuscenes)
        h1.add_child(self.load_nuscenes_button)
        file_section.add_child(h1)
        
        # MCTrack结果路径
        h2 = gui.Horiz(0.25 * em)
        h2.add_child(gui.Label("Tracking Results:"))
        self.tracking_path_text = gui.TextEdit()
        self.tracking_path_text.text_value = "results/nuscenes/latest/results.json"
        h2.add_child(self.tracking_path_text)
        
        self.load_tracking_button = gui.Button("Load Results")
        self.load_tracking_button.set_on_clicked(self._on_load_tracking)
        h2.add_child(self.load_tracking_button)
        file_section.add_child(h2)
        
        self.control_panel.add_child(file_section)
        
        # === 播放控制区域 ===
        play_section = gui.CollapsableVert("Playback Control", 0.25 * em, gui.Margins(em, 0, 0, 0))
        
        # Timeline slider
        timeline_h = gui.Horiz(0.25 * em)
        timeline_h.add_child(gui.Label("Timeline:"))
        self.timeline_slider = gui.Slider(gui.Slider.INT)
        self.timeline_slider.set_limits(0, 100)
        self.timeline_slider.set_on_value_changed(self._on_timeline_changed)
        timeline_h.add_child(self.timeline_slider)
        play_section.add_child(timeline_h)
        
        # Playback buttons
        controls_h = gui.Horiz(0.25 * em)
        self.play_button = gui.Button("Play")
        self.play_button.set_on_clicked(self._on_play_pause)
        controls_h.add_child(self.play_button)
        
        self.prev_button = gui.Button("Prev")
        self.prev_button.set_on_clicked(self._on_prev_frame)
        controls_h.add_child(self.prev_button)
        
        self.next_button = gui.Button("Next")
        self.next_button.set_on_clicked(self._on_next_frame)
        controls_h.add_child(self.next_button)
        
        play_section.add_child(controls_h)
        
        # Playback speed
        speed_h = gui.Horiz(0.25 * em)
        speed_h.add_child(gui.Label("Speed:"))
        self.speed_slider = gui.Slider(gui.Slider.DOUBLE)
        self.speed_slider.set_limits(0.1, 3.0)
        self.speed_slider.double_value = 1.0
        self.speed_slider.set_on_value_changed(self._on_speed_changed)
        speed_h.add_child(self.speed_slider)
        play_section.add_child(speed_h)
        
        self.control_panel.add_child(play_section)
        
        # === 显示设置区域 ===
        display_section = gui.CollapsableVert("Display Settings", 0.25 * em, gui.Margins(em, 0, 0, 0))
        
        # Display toggles
        self.show_pc_checkbox = gui.Checkbox("Show Point Cloud")
        self.show_pc_checkbox.checked = True
        self.show_pc_checkbox.set_on_checked(self._on_show_pc_changed)
        display_section.add_child(self.show_pc_checkbox)
        
        self.show_boxes_checkbox = gui.Checkbox("Show Tracking Boxes")
        self.show_boxes_checkbox.checked = True
        self.show_boxes_checkbox.set_on_checked(self._on_show_boxes_changed)
        display_section.add_child(self.show_boxes_checkbox)
        
        self.show_traj_checkbox = gui.Checkbox("Show Trajectories")
        self.show_traj_checkbox.checked = True
        self.show_traj_checkbox.set_on_checked(self._on_show_traj_changed)
        display_section.add_child(self.show_traj_checkbox)
        
        # Point cloud size
        pc_size_h = gui.Horiz(0.25 * em)
        pc_size_h.add_child(gui.Label("Point Size:"))
        self.pc_size_slider = gui.Slider(gui.Slider.DOUBLE)
        self.pc_size_slider.set_limits(0.5, 10.0)
        self.pc_size_slider.double_value = 2.0
        self.pc_size_slider.set_on_value_changed(self._on_pc_size_changed)
        pc_size_h.add_child(self.pc_size_slider)
        display_section.add_child(pc_size_h)
        
        # Trajectory length
        traj_len_h = gui.Horiz(0.25 * em)
        traj_len_h.add_child(gui.Label("Traj Length:"))
        self.traj_len_slider = gui.Slider(gui.Slider.INT)
        self.traj_len_slider.set_limits(5, 50)
        self.traj_len_slider.int_value = 20
        self.traj_len_slider.set_on_value_changed(self._on_traj_len_changed)
        traj_len_h.add_child(self.traj_len_slider)
        display_section.add_child(traj_len_h)
        
        self.control_panel.add_child(display_section)
        
        # === 场景信息区域 ===
        info_section = gui.CollapsableVert("Scene Info", 0.25 * em, gui.Margins(em, 0, 0, 0))
        info_section.set_is_open(False)
        
        self.info_text = gui.Label("Waiting for data...")
        info_section.add_child(self.info_text)
        
        self.control_panel.add_child(info_section)
        
    def _on_layout(self, layout_context):
        """布局回调函数"""
        r = self.window.content_rect
        
        # 控制面板宽度
        panel_width = 20 * layout_context.theme.font_size
        panel_height = min(r.height, 
                          self.control_panel.calc_preferred_size(
                              layout_context, gui.Widget.Constraints()).height)
        
        # 3D场景占据剩余空间
        scene_width = r.width - panel_width
        self.scene_widget.frame = gui.Rect(r.x, r.y, scene_width, r.height)
        
        # 控制面板在右侧
        self.control_panel.frame = gui.Rect(r.x + scene_width, r.y, 
                                          panel_width, panel_height)
    
    def _apply_visualization_settings(self):
        """应用可视化设置"""
        # 设置背景
        self.scene_widget.scene.set_background([0.1, 0.1, 0.1, 1.0])
        self.scene_widget.scene.show_axes(True)
        
        # 设置光照
        self.scene_widget.scene.scene.set_sun_light(
            [0.577, -0.577, -0.577], [1, 1, 1], 75000)
        self.scene_widget.scene.scene.enable_sun_light(True)
        
    def _on_sun_dir_changed(self, sun_dir):
        """太阳光方向改变回调"""
        pass
        
    # === 数据加载相关方法 ===
    def _on_load_nuscenes(self):
        """加载nuScenes数据"""
        if not NUSCENES_AVAILABLE:
            self._show_message("错误", "nuscenes-devkit未安装")
            return
            
        path = self.nuscenes_path_text.text_value
        if not os.path.exists(path):
            self._show_message("错误", f"路径不存在: {path}")
            return
            
        try:
            # 尝试加载不同版本
            for version in ['v1.0-trainval', 'v1.0-mini']:
                try:
                    self.nusc = NuScenes(version=version, dataroot=path, verbose=True)
                    break
                except:
                    continue
                    
            if self.nusc is None:
                raise Exception("无法加载任何nuScenes版本")
                
            # 加载第一个场景
            if len(self.nusc.scene) > 0:
                self.scene_token = self.nusc.scene[0]['token']
                self._load_scene_data()
                self._update_info_text()
                self._show_message("成功", f"已加载nuScenes数据集 ({self.nusc.version})")
            else:
                raise Exception("数据集中没有场景")
                
        except Exception as e:
            self._show_message("错误", f"加载nuScenes失败: {str(e)}")
            
    def _on_load_tracking(self):
        """加载跟踪结果"""
        path = self.tracking_path_text.text_value
        if not os.path.exists(path):
            self._show_message("错误", f"文件不存在: {path}")
            return
            
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            if 'results' in data:
                self.tracking_data = data['results']
            else:
                self.tracking_data = data
                
            self._update_info_text()
            self._show_message("成功", "已加载跟踪结果")
            
            # 如果数据都加载了，显示第一帧
            if self.nusc is not None and self.tracking_data is not None:
                self._show_frame(0)
                
        except Exception as e:
            self._show_message("错误", f"加载跟踪结果失败: {str(e)}")
            
    def _load_scene_data(self):
        """加载场景数据"""
        if self.nusc is None or self.scene_token is None:
            return
            
        scene = self.nusc.get('scene', self.scene_token)
        
        # 获取所有sample tokens
        self.sample_tokens = []
        sample_token = scene['first_sample_token']
        while sample_token:
            self.sample_tokens.append(sample_token)
            sample = self.nusc.get('sample', sample_token)
            sample_token = sample['next']
            
        self.settings.total_frames = len(self.sample_tokens)
        self.settings.current_frame = 0
        
        # 更新时间轴滑块
        if self.settings.total_frames > 0:
            self.timeline_slider.set_limits(0, self.settings.total_frames - 1)
            self.timeline_slider.int_value = 0
            
    # === 播放控制相关方法 ===
    def _on_timeline_changed(self, value):
        """时间轴滑块改变"""
        frame_id = int(value)
        if frame_id != self.settings.current_frame:
            self.settings.current_frame = frame_id
            self._show_frame(frame_id)
            
    def _on_play_pause(self):
        """播放/暂停按钮"""
        self.is_playing = not self.is_playing
        self.play_button.text = "Pause" if self.is_playing else "Play"
        
        if self.is_playing:
            self.last_play_time = time.time()
            self._start_play_timer()
            
    def _on_prev_frame(self):
        """上一帧"""
        if self.settings.current_frame > 0:
            self.settings.current_frame -= 1
            self.timeline_slider.int_value = self.settings.current_frame
            self._show_frame(self.settings.current_frame)
            
    def _on_next_frame(self):
        """下一帧"""
        if self.settings.current_frame < self.settings.total_frames - 1:
            self.settings.current_frame += 1
            self.timeline_slider.int_value = self.settings.current_frame
            self._show_frame(self.settings.current_frame)
            
    def _on_speed_changed(self, value):
        """播放速度改变"""
        self.settings.play_speed = value
        
    def _start_play_timer(self):
        """开始播放计时器"""
        if not self.is_playing:
            return
            
        # 计算是否需要前进到下一帧
        current_time = time.time()
        elapsed = current_time - self.last_play_time
        
        # 基于播放速度计算帧间隔 (假设原始帧率为10fps)
        frame_interval = 0.1 / self.settings.play_speed
        
        if elapsed >= frame_interval:
            if self.settings.current_frame < self.settings.total_frames - 1:
                self.settings.current_frame += 1
                self.timeline_slider.int_value = self.settings.current_frame
                self._show_frame(self.settings.current_frame)
                self.last_play_time = current_time
            else:
                # Playback ended
                self.is_playing = False
                self.play_button.text = "Play"
                
        # 继续计时器
        if self.is_playing:
            gui.Application.instance.post_to_main_thread(
                self.window, lambda: self._start_play_timer())
                
    # === 显示设置相关方法 ===
    def _on_show_pc_changed(self, checked):
        """显示点云开关"""
        self.settings.show_point_cloud = checked
        self._update_display()
        
    def _on_show_boxes_changed(self, checked):
        """显示跟踪框开关"""
        self.settings.show_tracking_boxes = checked
        self._update_display()
        
    def _on_show_traj_changed(self, checked):
        """显示轨迹开关"""
        self.settings.show_trajectories = checked
        self._update_display()
        
    def _on_pc_size_changed(self, value):
        """点云大小改变"""
        self.settings.point_size = value
        self._update_point_cloud_material()
        
    def _on_traj_len_changed(self, value):
        """轨迹长度改变"""
        self.settings.trajectory_length = int(value)
        self._update_display()
        
    # === 可视化核心方法 ===
    def _show_frame(self, frame_id: int):
        """显示指定帧"""
        if (self.nusc is None or frame_id >= len(self.sample_tokens) or 
            frame_id < 0):
            return
            
        # 清除当前几何对象
        self._clear_scene()
        
        sample_token = self.sample_tokens[frame_id]
        sample = self.nusc.get('sample', sample_token)
        
        # 显示点云
        if self.settings.show_point_cloud:
            self._show_point_cloud(sample)
            
        # 显示跟踪结果
        if self.settings.show_tracking_boxes and self.tracking_data is not None:
            self._show_tracking_boxes(sample_token, frame_id)
            
        # 显示轨迹
        if self.settings.show_trajectories and self.tracking_data is not None:
            self._show_trajectories(frame_id)
            
        # 更新相机视角（仅第一次）
        if frame_id == 0:
            self._setup_camera()
            
        self._update_info_text()
        
    def _show_point_cloud(self, sample):
        """显示点云"""
        try:
            lidar_token = sample['data']['LIDAR_TOP']
            lidar_data = self.nusc.get('sample_data', lidar_token)
            
            # 加载点云文件
            pc_path = os.path.join(self.nusc.dataroot, lidar_data['filename'])
            if os.path.exists(pc_path):
                # nuScenes点云格式为.pcd.bin (32-bit float, x,y,z,intensity,ring)
                if pc_path.endswith('.pcd.bin'):
                    points_data = np.fromfile(pc_path, dtype=np.float32).reshape(-1, 5)
                    points = points_data[:, :3]  # 只取x,y,z坐标
                    
                    # 可选：使用intensity作为颜色
                    if points_data.shape[1] >= 4:
                        intensities = points_data[:, 3]
                        # 归一化intensity到0-1范围
                        intensities_norm = (intensities - intensities.min()) / (intensities.max() - intensities.min() + 1e-8)
                        # 创建基于intensity的颜色
                        colors = np.zeros((len(points), 3))
                        colors[:, 0] = intensities_norm  # 红色通道
                        colors[:, 1] = intensities_norm * 0.5  # 绿色通道
                        colors[:, 2] = intensities_norm * 0.3  # 蓝色通道
                    else:
                        # 使用默认颜色
                        colors = np.tile(self.settings.point_cloud_color, (len(points), 1))
                else:
                    pcd = o3d.io.read_point_cloud(pc_path)
                    points = np.asarray(pcd.points)
                    colors = np.tile(self.settings.point_cloud_color, (len(points), 1))
                    
                # 创建点云对象
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(points)
                pcd.colors = o3d.utility.Vector3dVector(colors)
                
                # 创建材质
                material = rendering.MaterialRecord()
                material.point_size = self.settings.point_size
                material.shader = "unlitPoints"
                
                # 添加到场景
                self.scene_widget.scene.add_geometry("point_cloud", pcd, material)
                self.current_geometries["point_cloud"] = True
                print(f"Loaded point cloud: {len(points)} points from {pc_path}")
            else:
                print(f"Point cloud file not found: {pc_path}")
                
        except Exception as e:
            print(f"Error loading point cloud: {str(e)}")
            # 创建一个简单的测试点云
            test_points = np.random.rand(1000, 3) * 50 - 25  # -25到25的随机点
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(test_points)
            pcd.colors = o3d.utility.Vector3dVector(np.tile([0.7, 0.7, 0.7], (len(test_points), 1)))
            
            material = rendering.MaterialRecord()
            material.point_size = self.settings.point_size
            material.shader = "unlitPoints"
            
            self.scene_widget.scene.add_geometry("point_cloud", pcd, material)
            self.current_geometries["point_cloud"] = True
            print("Loaded test point cloud due to error")
            
    def _show_tracking_boxes(self, sample_token: str, frame_id: int):
        """显示跟踪框"""
        if sample_token not in self.tracking_data:
            return
            
        boxes_data = self.tracking_data[sample_token]
        
        for i, box_data in enumerate(boxes_data):
            track_id = box_data.get('tracking_id', i)
            
            # 获取3D框参数
            translation = box_data['translation']
            size = box_data['size'] 
            rotation = box_data['rotation']
            
            # 创建3D边界框
            bbox = self._create_bbox_lineset(translation, size, rotation)
            
            # 设置颜色（基于track_id）
            color_idx = track_id % len(self.settings.color_palette)
            color = self.settings.color_palette[color_idx]
            bbox.paint_uniform_color(color)
            
            # 添加到场景
            bbox_name = f"bbox_{track_id}_{i}"
            material = rendering.MaterialRecord()
            material.line_width = self.settings.box_line_width
            material.shader = "unlitLine"
            
            self.scene_widget.scene.add_geometry(bbox_name, bbox, material)
            self.current_geometries[bbox_name] = True
            
    def _show_trajectories(self, current_frame: int):
        """显示轨迹"""
        if current_frame == 0:
            return
            
        # 收集轨迹数据
        trajectories = {}  # track_id -> [(x, y, z), ...]
        
        start_frame = max(0, current_frame - self.settings.trajectory_length)
        
        for frame_idx in range(start_frame, current_frame + 1):
            if frame_idx >= len(self.sample_tokens):
                continue
                
            sample_token = self.sample_tokens[frame_idx]
            if sample_token not in self.tracking_data:
                continue
                
            boxes_data = self.tracking_data[sample_token]
            
            for box_data in boxes_data:
                track_id = box_data.get('tracking_id', -1)
                if track_id == -1:
                    continue
                    
                translation = box_data['translation']
                
                if track_id not in trajectories:
                    trajectories[track_id] = []
                trajectories[track_id].append(translation)
                
        # 创建轨迹线条
        for track_id, points in trajectories.items():
            if len(points) < 2:
                continue
                
            # 创建线段
            line_set = o3d.geometry.LineSet()
            line_set.points = o3d.utility.Vector3dVector(points)
            
            # 创建线段连接
            lines = []
            for i in range(len(points) - 1):
                lines.append([i, i + 1])
            line_set.lines = o3d.utility.Vector2iVector(lines)
            
            # 设置颜色（渐变透明度效果）
            color_idx = track_id % len(self.settings.color_palette)
            base_color = self.settings.color_palette[color_idx]
            
            colors = []
            for i in range(len(lines)):
                alpha = (i + 1) / len(lines)  # 越新的轨迹越明亮
                color = [c * alpha for c in base_color]
                colors.append(color)
            line_set.colors = o3d.utility.Vector3dVector(colors)
            
            # 添加到场景
            traj_name = f"trajectory_{track_id}"
            material = rendering.MaterialRecord()
            material.line_width = 1.5
            material.shader = "unlitLine"
            
            self.scene_widget.scene.add_geometry(traj_name, line_set, material)
            self.current_geometries[traj_name] = True
            
    def _create_bbox_lineset(self, translation, size, rotation) -> o3d.geometry.LineSet:
        """创建3D边界框线条"""
        # 创建标准3D框
        l, w, h = size
        
        # 8个顶点
        vertices = np.array([
            [-l/2, -w/2, -h/2], [l/2, -w/2, -h/2], [l/2, w/2, -h/2], [-l/2, w/2, -h/2],  # 底面
            [-l/2, -w/2, h/2],  [l/2, -w/2, h/2],  [l/2, w/2, h/2],  [-l/2, w/2, h/2]    # 顶面
        ])
        
        # 应用旋转
        from scipy.spatial.transform import Rotation as R
        if len(rotation) == 4:  # 四元数
            r = R.from_quat(rotation)
        else:  # 欧拉角
            r = R.from_euler('xyz', rotation)
        vertices = r.apply(vertices)
        
        # 应用平移
        vertices += np.array(translation)
        
        # 创建边线连接
        lines = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # 底面
            [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面
            [0, 4], [1, 5], [2, 6], [3, 7]   # 垂直边
        ]
        
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(vertices)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        
        return line_set
        
    def _clear_scene(self):
        """清除场景中的几何对象"""
        for name in self.current_geometries.keys():
            if self.scene_widget.scene.has_geometry(name):
                self.scene_widget.scene.remove_geometry(name)
        self.current_geometries.clear()
        
    def _setup_camera(self):
        """设置相机视角"""
        bounds = o3d.geometry.AxisAlignedBoundingBox([-50, -50, -5], [50, 50, 5])
        center = [0, 0, 0]
        self.scene_widget.setup_camera(60, bounds, center)
        
    def _update_display(self):
        """更新显示"""
        if self.settings.total_frames > 0:
            self._show_frame(self.settings.current_frame)
            
    def _update_point_cloud_material(self):
        """更新点云材质"""
        if "point_cloud" in self.current_geometries:
            material = rendering.MaterialRecord()
            material.point_size = self.settings.point_size
            material.shader = "unlitPoints"
            self.scene_widget.scene.update_material(material)
            
    def _update_info_text(self):
        """更新信息文本"""
        info_lines = []
        
        if self.nusc is not None:
            info_lines.append(f"数据集: {self.nusc.version}")
            info_lines.append(f"场景数: {len(self.nusc.scene)}")
            
        if self.settings.total_frames > 0:
            info_lines.append(f"总帧数: {self.settings.total_frames}")
            info_lines.append(f"当前帧: {self.settings.current_frame + 1}")
            
        if self.tracking_data is not None:
            info_lines.append(f"跟踪结果已加载")
            
        if len(info_lines) == 0:
            info_lines.append("Waiting for data...")
            
        self.info_text.text = "\n".join(info_lines)
        
    def _show_message(self, title: str, message: str):
        """显示消息对话框"""
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
        """运行可视化工具"""
        gui.Application.instance.run()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCTrack Visualizer")
    parser.add_argument("--nuscenes-path", type=str, 
                       default="data/nuScenes/datasets",
                       help="nuScenes数据集路径")
    parser.add_argument("--tracking-results", type=str,
                       default="results/nuscenes/latest/results.json", 
                       help="MCTrack跟踪结果文件路径")
    parser.add_argument("--width", type=int, default=1920, 
                       help="窗口宽度")
    parser.add_argument("--height", type=int, default=1080,
                       help="窗口高度")
    
    args = parser.parse_args()
    
    # 创建并运行可视化工具
    visualizer = MCTrackVisualizer(args.width, args.height)
    
    # 设置默认路径
    visualizer.nuscenes_path_text.text_value = args.nuscenes_path
    visualizer.tracking_path_text.text_value = args.tracking_results
    
    print("MCTrack Visualizer 启动")
    print("="*50)
    print("功能:")
    print("1. 加载nuScenes数据集和MCTrack跟踪结果")
    print("2. 时间轴拖拽控制")
    print("3. 播放/暂停控制")
    print("4. 可视化设置调整")
    print("5. 点云、跟踪框、轨迹同步显示")
    print("="*50)
    
    visualizer.run()


if __name__ == "__main__":
    main()