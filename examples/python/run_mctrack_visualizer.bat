@echo off
echo ========================================
echo     MCTrack 可视化工具启动脚本
echo ========================================
echo.

REM 激活conda环境
echo 激活MCTrack环境...
call conda activate MCTrack
if %errorlevel% neq 0 (
    echo 错误: 无法激活MCTrack环境
    echo 请确保已创建MCTrack conda环境
    pause
    exit /b 1
)

REM 切换到脚本目录
cd /d "%~dp0"
echo 当前目录: %cd%

REM 检查Python文件是否存在
if not exist "mctrack_visualizer.py" (
    echo 错误: 找不到 mctrack_visualizer.py
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

REM 显示使用说明
echo.
echo 使用说明:
echo 1. 在GUI中设置nuScenes数据集路径
echo 2. 设置MCTrack跟踪结果文件路径  
echo 3. 点击对应的"加载"按钮
echo 4. 使用时间轴和播放控制进行可视化
echo.
echo 默认路径:
echo - nuScenes: D:\OneDrive\NUS\ME5400\MCTrack\data\nuScenes\datasets
echo - 跟踪结果: D:\OneDrive\NUS\ME5400\MCTrack\results\nuscenes\latest\results.json
echo.

REM 询问是否先运行测试
set /p test_choice="是否先运行功能测试? (y/n): "
if /i "%test_choice%"=="y" (
    echo.
    echo 运行功能测试...
    python test_mctrack_visualizer.py
    if %errorlevel% neq 0 (
        echo.
        echo 测试失败，请检查错误信息
        pause
        exit /b 1
    )
    echo.
    echo 测试通过! 继续启动可视化工具...
    echo.
)

REM 启动可视化工具
echo 启动MCTrack可视化工具...
echo.
python mctrack_visualizer.py --width 1920 --height 1080

REM 检查启动结果
if %errorlevel% neq 0 (
    echo.
    echo 错误: 可视化工具启动失败
    echo 错误代码: %errorlevel%
    echo.
    echo 可能的解决方案:
    echo 1. 检查Python环境和依赖包
    echo 2. 运行 test_mctrack_visualizer.py 进行诊断
    echo 3. 检查数据路径是否正确
    pause
    exit /b 1
)

echo.
echo MCTrack可视化工具已退出
pause