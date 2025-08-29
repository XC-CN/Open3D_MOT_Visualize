<p align="center">
<img src="https://raw.githubusercontent.com/isl-org/Open3D/main/docs/_static/open3d_logo_horizontal.png" width="320" />
</p>

# Open3D：用于3D数据处理的现代库

<h4>
    <a href="https://www.open3d.org">主页</a> |
    <a href="https://www.open3d.org/docs">文档</a> |
    <a href="https://www.open3d.org/docs/release/getting_started.html">快速开始</a> |
    <a href="https://www.open3d.org/docs/release/compilation.html">编译</a> |
    <a href="https://www.open3d.org/docs/release/index.html#python-api-index">Python</a> |
    <a href="https://www.open3d.org/docs/release/cpp_api.html">C++</a> |
    <a href="https://github.com/isl-org/Open3D-ML">Open3D-ML</a> |
    <a href="https://github.com/isl-org/Open3D/releases">查看器</a> |
    <a href="https://www.open3d.org/docs/release/contribute/contribute.html">贡献</a> |
    <a href="https://www.youtube.com/channel/UCRJBlASPfPBtPXJSPffJV-w">演示</a> |
    <a href="https://github.com/isl-org/Open3D/discussions">论坛</a>
</h4>

Open3D是一个开源库，支持快速开发处理3D数据的软件。Open3D前端在C++和Python中暴露了一组精心选择的数据结构和算法。后端经过高度优化，并设置为并行化。我们欢迎来自开源社区的贡献。

[![Ubuntu CI](https://github.com/isl-org/Open3D/actions/workflows/ubuntu.yml/badge.svg)](https://github.com/isl-org/Open3D/actions?query=workflow%3A%22Ubuntu+CI%22)
[![macOS CI](https://github.com/isl-org/Open3D/actions/workflows/macos.yml/badge.svg)](https://github.com/isl-org/Open3D/actions?query=workflow%3A%22macOS+CI%22)
[![Windows CI](https://github.com/isl-org/Open3D/actions/workflows/windows.yml/badge.svg)](https://github.com/isl-org/Open3D/actions?query=workflow%3A%22Windows+CI%22)

**Open3D的核心功能包括：**

-   3D数据结构
-   3D数据处理算法
-   场景重建
-   表面对齐
-   3D可视化
-   基于物理的渲染（PBR）
-   支持PyTorch和TensorFlow的3D机器学习
-   核心3D操作的GPU加速
-   提供C++和Python版本

以下是Open3D不同组件的简要概述，以及它们如何协同工作以实现完整的端到端管道：

![Open3D_layers](https://github.com/isl-org/Open3D/assets/41028320/e9b8645a-a823-4d78-8310-e85207bbc3e4)

更多信息，请访问[Open3D文档](https://www.open3d.org/docs)。

也请查看这本介绍现代3D数据处理的优秀书籍，其中介绍了Open3D：

<img src="https://learning.oreilly.com/covers/urn:orm:book:9781098161323/400w/" width="240" alt="3D Data Science with Python" />

[使用Python进行3D数据科学](https://learning.oreilly.com/library/view/3d-data-science/9781098161323/)
作者：[Dr. Florent Poux](https://www.graphics.rwth-aachen.de/person/306/)

作者的话：

> 在整本书中，我通过实际示例和代码样本展示了Open3D如何实现高效的点云处理、网格操作和3D可视化。读者学习如何在实际的3D数据科学工作流程中利用Open3D强大的注册、分割和特征提取能力。

## Python快速开始

预构建的pip包支持Ubuntu 20.04+、macOS 10.15+和Windows 10+（64位），Python版本3.8-3.11。

```bash
# 安装
pip install open3d       # 或者
pip install open3d-cpu   # 在x86_64 Linux上的较小CPU专用wheel（v0.17+）

# 验证安装
python -c "import open3d as o3d; print(o3d.__version__)"

# Python API
python -c "import open3d as o3d; \
           mesh = o3d.geometry.TriangleMesh.create_sphere(); \
           mesh.compute_vertex_normals(); \
           o3d.visualization.draw(mesh, raw_mode=True)"

# Open3D CLI
open3d example visualization/draw
```

要获得Open3D的最新功能，请安装[开发版pip包](https://www.open3d.org/docs/latest/getting_started.html#development-version-pip)。
要从源代码编译Open3D，请参考[从源代码编译](https://www.open3d.org/docs/release/compilation.html)。

## C++快速开始

查看以下链接开始使用Open3D C++ API

-   下载Open3D二进制包：[发布版](https://github.com/isl-org/Open3D/releases)或[最新开发版本](https://www.open3d.org/docs/latest/getting_started.html#c)
-   [从源代码编译Open3D](https://www.open3d.org/docs/release/compilation.html)
-   [Open3D C++ API](https://www.open3d.org/docs/release/cpp_api.html)

要在您的C++项目中使用Open3D，请查看以下示例

-   [在CMake中查找预安装的Open3D包](https://github.com/isl-org/open3d-cmake-find-package)
-   [将Open3D用作CMake外部项目](https://github.com/isl-org/open3d-cmake-external-project)

## Open3D-Viewer应用

<img width="480" src="https://raw.githubusercontent.com/isl-org/Open3D/main/docs/_static/open3d_viewer.png">

Open3D-Viewer是一个独立的3D查看器应用，可在Debian（Ubuntu）、macOS和Windows上使用。从[发布页面](https://github.com/isl-org/Open3D/releases)下载Open3D Viewer。

## Open3D-ML

<img width="480" src="https://raw.githubusercontent.com/isl-org/Open3D-ML/main/docs/images/getting_started_ml_visualizer.gif">

Open3D-ML是Open3D的扩展，用于3D机器学习任务。它构建在Open3D核心库之上，并扩展了用于3D数据处理的机器学习工具。要试用它，请安装带有PyTorch或TensorFlow的Open3D，并查看[Open3D-ML](https://github.com/isl-org/Open3D-ML)。

## 交流渠道

-   [GitHub Issue](https://github.com/isl-org/Open3D/issues)：错误报告、功能请求等。
-   [论坛](https://github.com/isl-org/Open3D/discussions)：关于Open3D使用的讨论。
-   [Discord聊天](https://discord.gg/D35BGvn)：在线聊天、讨论和与其他用户和开发者的协作。

## 引用

如果您使用Open3D，请引用[我们的工作](https://arxiv.org/abs/1801.09847)。

```bib
@article{Zhou2018,
    author    = {Qian-Yi Zhou and Jaesik Park and Vladlen Koltun},
    title     = {{Open3D}: {A} Modern Library for {3D} Data Processing},
    journal   = {arXiv:1801.09847},
    year      = {2018},
}
```
