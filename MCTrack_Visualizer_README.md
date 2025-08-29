# MCTrack 可视化工具

基于Open3D开发的专业多目标跟踪可视化工具，支持nuScenes数据集和MCTrack跟踪结果的同步可视化。

![MCTrack Visualizer](docs/mctrack_visualizer_screenshot.png)

## ✨ 核心功能

- **🎬 时间轴控制**: 可拖拽进度条，支持任意帧跳转
- **🚀 播放控制**: 播放/暂停，可调节播放速度 
- **🎯 3D可视化**: 点云、跟踪框、轨迹同步显示
- **🎨 实时调节**: 点云大小、轨迹长度等参数实时调整
- **🌈 智能着色**: 基于跟踪ID的自动颜色分配
- **📊 信息面板**: 实时显示场景和跟踪统计信息

## 🛠 环境要求

### Python环境
```bash
Python >= 3.8
```

### 必需依赖
```bash
pip install open3d>=0.18.0
pip install numpy
pip install scipy
```

### 可选依赖（用于nuScenes数据加载）
```bash
pip install nuscenes-devkit
```

## 🚀 快速开始

### 1. 启动可视化工具
```bash
cd D:\OneDrive\NUS\ME5400\Open3D_MOT_Visualize\examples\python
python mctrack_visualizer.py
```

### 2. 使用命令行参数
```bash
python mctrack_visualizer.py \
    --nuscenes-path "D:\OneDrive\NUS\ME5400\MCTrack\data\nuScenes\datasets" \
    --tracking-results "D:\OneDrive\NUS\ME5400\MCTrack\results\nuscenes\latest\results.json" \
    --width 1920 \
    --height 1080
```

### 3. GUI操作流程

#### 步骤1: 数据加载
1. **加载nuScenes数据**:
   - 在"nuScenes路径"中输入数据集路径
   - 点击"加载nuScenes"按钮
   - 等待数据集加载完成

2. **加载跟踪结果**:
   - 在"跟踪结果"中输入MCTrack结果文件路径
   - 点击"加载跟踪结果"按钮

#### 步骤2: 播放控制
- **时间轴**: 拖拽进度条跳转到任意帧
- **播放按钮**: 点击播放/暂停
- **帧控制**: 使用"上一帧"/"下一帧"按钮
- **速度调节**: 调整播放速度滑块（0.1x - 3.0x）

#### 步骤3: 显示设置
- **显示选项**: 
  - ☑️ 显示点云
  - ☑️ 显示跟踪框  
  - ☑️ 显示轨迹
- **参数调节**:
  - 点云大小: 0.5 - 10.0
  - 轨迹长度: 5 - 50帧

## 📁 数据格式要求

### nuScenes数据集结构
```
data/nuScenes/datasets/
├── maps/
├── samples/
├── sweeps/
├── v1.0-trainval/
│   ├── category.json
│   ├── sample.json
│   └── ...
└── v1.0-mini/  (或其他版本)
```

### MCTrack结果格式
```json
{
  "results": {
    "sample_token_1": [
      {
        "translation": [x, y, z],
        "size": [length, width, height], 
        "rotation": [qw, qx, qy, qz],
        "tracking_id": 123,
        "tracking_name": "car",
        "tracking_score": 0.95
      }
    ]
  }
}
```

## 🎮 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Space` | 播放/暂停 |
| `←/→` | 上一帧/下一帧 |
| `↑/↓` | 调整播放速度 |
| `R` | 重置视角 |
| `1-9` | 快速跳转到场景的1/9, 2/9, ..., 9/9位置 |

## 🔧 高级配置

### 自定义颜色方案
编辑 `mctrack_visualizer.py` 中的颜色设置:
```python
def _generate_color_palette(self, num_colors: int):
    # 自定义你的颜色方案
    colors = []
    for i in range(num_colors):
        # RGB颜色值 [0-1]
        colors.append([r, g, b])
    return colors
```

### 调整可视化参数
```python
class MCTrackSettings:
    def __init__(self):
        self.point_size = 2.0              # 点云大小
        self.box_line_width = 2.0          # 边界框线宽
        self.trajectory_length = 20        # 轨迹长度
        self.play_speed = 1.0             # 默认播放速度
```

## 🐛 问题排查

### 常见问题

**1. "nuscenes-devkit not available"**
```bash
pip install nuscenes-devkit
```

**2. "路径不存在"**
- 检查nuScenes数据集路径是否正确
- 确保包含v1.0-trainval或v1.0-mini文件夹

**3. "无法加载任何nuScenes版本"**
- 确认数据集完整性
- 检查文件权限

**4. 跟踪结果不显示**
- 检查MCTrack结果文件格式
- 确认sample_token匹配

**5. 界面卡顿**
- 降低点云大小
- 减少轨迹长度
- 关闭不必要的显示选项

### 性能优化建议

1. **大数据集优化**:
   - 使用SSD存储
   - 增加系统内存
   - 使用GPU加速版本的Open3D

2. **显示优化**:
   - 适当降低点云密度
   - 限制同时显示的轨迹数量
   - 调整渲染质量设置

## 📈 扩展开发

### 添加新的数据格式支持
1. 继承基础数据加载器
2. 实现自定义数据解析方法
3. 注册到可视化工具

### 自定义可视化组件
1. 扩展几何对象类型
2. 添加新的交互控件
3. 实现自定义渲染效果

## 🤝 贡献指南

欢迎提交Issue和Pull Request来完善这个工具！

### 开发环境设置
```bash
git clone https://github.com/XC-CN/Open3D_MOT_Visualize.git
cd Open3D_MOT_Visualize
pip install -r requirements.txt
```

### 提交规范
- 遵循PEP 8代码规范
- 添加必要的注释和文档
- 提供测试用例

## 📝 更新日志

### v1.0.0 (2025-01-29)
- ✅ 基础可视化功能
- ✅ 时间轴拖拽控制
- ✅ nuScenes数据集支持
- ✅ MCTrack结果显示
- ✅ 轨迹可视化
- ✅ 播放控制

### 计划功能
- 🔄 多场景切换
- 🔄 相机视图同步显示
- 🔄 导出功能（图像/视频）
- 🔄 批量处理模式
- 🔄 实时跟踪结果接收

## 📄 许可证

本项目基于MIT许可证开源。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Open3D](http://www.open3d.org/) - 3D数据处理和可视化库
- [nuScenes](https://www.nuscenes.org/) - 自动驾驶数据集
- [MCTrack](https://github.com/megvii-research/MCTrack) - 多目标跟踪算法

---

**如有问题或建议，请提交Issue或联系开发者！** 🚀