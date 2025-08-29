#!/usr/bin/env python3
"""
MCTrack可视化工具测试脚本
用于验证可视化工具的功能和性能
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

def create_mock_tracking_data(num_frames: int = 10, num_tracks: int = 5) -> dict:
    """创建模拟跟踪数据用于测试"""
    results = {}
    
    # 生成模拟的sample tokens
    sample_tokens = [f"sample_token_{i:03d}" for i in range(num_frames)]
    
    # 为每个帧生成跟踪结果
    for frame_idx, token in enumerate(sample_tokens):
        frame_results = []
        
        for track_id in range(num_tracks):
            # 模拟车辆在环形轨道上移动
            t = frame_idx / num_frames * 2 * np.pi
            radius = 20 + track_id * 5  # 不同半径的圆形轨迹
            
            x = radius * np.cos(t + track_id * 0.5)
            y = radius * np.sin(t + track_id * 0.5) 
            z = 0.5  # 地面高度
            
            # 车辆朝向
            yaw = t + track_id * 0.5 + np.pi/2
            quat = [np.cos(yaw/2), 0, 0, np.sin(yaw/2)]  # [qw, qx, qy, qz]
            
            box_data = {
                "translation": [x, y, z],
                "size": [4.5, 2.0, 1.8],  # 车辆尺寸 [长, 宽, 高]
                "rotation": quat,
                "tracking_id": track_id,
                "tracking_name": "car",
                "tracking_score": 0.8 + 0.2 * np.random.random()
            }
            frame_results.append(box_data)
            
        results[token] = frame_results
        
    return {"results": results}


def test_dependencies():
    """测试依赖包是否正确安装"""
    print("🔍 检查依赖包...")
    
    dependencies = {
        "open3d": "Open3D",
        "numpy": "NumPy", 
        "scipy": "SciPy"
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {name} - 已安装")
        except ImportError:
            print(f"  ❌ {name} - 未安装")
            missing.append(module)
            
    # 检查可选依赖
    try:
        __import__("nuscenes")
        print("  ✅ nuScenes-devkit - 已安装")
    except ImportError:
        print("  ⚠️  nuScenes-devkit - 未安装 (可选)")
        
    if missing:
        print(f"\n❌ 缺少必需依赖: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        return False
    else:
        print("\n✅ 所有必需依赖已安装")
        return True


def test_visualizer_import():
    """测试可视化工具是否能正确导入"""
    print("🔍 测试可视化工具导入...")
    
    try:
        import mctrack_visualizer
        print("  ✅ mctrack_visualizer 模块导入成功")
        
        # 测试主要类
        visualizer = mctrack_visualizer.MCTrackVisualizer(800, 600)
        print("  ✅ MCTrackVisualizer 类创建成功")
        
        settings = mctrack_visualizer.MCTrackSettings()
        print("  ✅ MCTrackSettings 类创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 导入失败: {str(e)}")
        return False


def create_test_data():
    """创建测试数据文件"""
    print("🔍 创建测试数据...")
    
    # 创建测试目录
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # 创建模拟跟踪结果
    tracking_data = create_mock_tracking_data(20, 8)  # 20帧，8个跟踪目标
    
    tracking_file = test_dir / "mock_tracking_results.json"
    with open(tracking_file, 'w') as f:
        json.dump(tracking_data, f, indent=2)
        
    print(f"  ✅ 测试跟踪数据已创建: {tracking_file}")
    
    # 创建简单的点云数据
    import open3d as o3d
    
    # 生成模拟地面点云
    ground_points = []
    for x in np.linspace(-50, 50, 100):
        for y in np.linspace(-50, 50, 100):
            if np.random.random() < 0.1:  # 稀疏采样
                ground_points.append([x, y, np.random.normal(0, 0.1)])
                
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(ground_points)
    
    pcd_file = test_dir / "mock_pointcloud.pcd"
    o3d.io.write_point_cloud(str(pcd_file), pcd)
    
    print(f"  ✅ 测试点云数据已创建: {pcd_file}")
    
    return tracking_file, pcd_file


def test_visualization():
    """测试可视化功能"""
    print("🔍 测试可视化功能...")
    
    try:
        import mctrack_visualizer
        import open3d.visualization.gui as gui
        
        # 初始化应用
        if not gui.Application.instance.initialize():
            print("  ❌ Open3D GUI初始化失败")
            return False
            
        print("  ✅ Open3D GUI初始化成功")
        
        # 创建可视化器
        visualizer = mctrack_visualizer.MCTrackVisualizer(800, 600)
        print("  ✅ 可视化器创建成功")
        
        # 测试设置
        visualizer.settings.show_point_cloud = True
        visualizer.settings.show_tracking_boxes = True  
        visualizer.settings.show_trajectories = True
        print("  ✅ 设置配置成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 可视化测试失败: {str(e)}")
        return False


def run_demo_mode():
    """运行演示模式"""
    print("🚀 启动演示模式...")
    
    try:
        # 创建测试数据
        tracking_file, pcd_file = create_test_data()
        
        print("\n📋 演示说明:")
        print("1. 可视化工具将启动并显示模拟数据")
        print("2. 8个车辆在圆形轨道上移动")
        print("3. 使用时间轴拖拽控制播放进度")
        print("4. 测试各种显示选项和参数调整")
        print("\n按任意键继续...")
        input()
        
        # 启动可视化工具
        import mctrack_visualizer
        
        visualizer = mctrack_visualizer.MCTrackVisualizer(1200, 800)
        
        # 设置测试数据路径
        visualizer.tracking_path_text.text_value = str(tracking_file)
        
        print("  ✅ 可视化工具已启动")
        print("  💡 提示: 点击'加载跟踪结果'按钮加载测试数据")
        
        # 运行GUI
        visualizer.run()
        
    except Exception as e:
        print(f"  ❌ 演示模式启动失败: {str(e)}")
        print(f"  详细错误: {type(e).__name__}: {str(e)}")


def main():
    """主测试函数"""
    print("🎯 MCTrack 可视化工具测试")
    print("=" * 50)
    
    # 测试依赖
    if not test_dependencies():
        return False
        
    print()
    
    # 测试导入
    if not test_visualizer_import():
        return False
        
    print()
    
    # 测试可视化
    if not test_visualization():
        return False
        
    print()
    print("✅ 所有测试通过!")
    print()
    
    # 询问是否运行演示
    choice = input("🤔 是否运行演示模式? (y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        print()
        run_demo_mode()
    else:
        print("\n🎉 测试完成! 可以手动运行 mctrack_visualizer.py")
        
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试过程中出现意外错误: {str(e)}")
        sys.exit(1)