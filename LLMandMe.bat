@echo off
echo ========================================================
echo       正在启动全栈开发环境 (Vue + FastAPI)
echo       项目路径: F:\LLMandME
echo ========================================================

:: 1. 切换到项目根目录 (/d 参数允许跨盘符切换)
cd /d .\

:: 2. 打开 VS Code (需要在根目录下)
echo [1/4] 正在打开 VS Code...
call code .

:: 3. 启动后端 (新建一个窗口，保留运行)
:: "FastAPI Backend" 是窗口标题
:: /k 表示执行完命令后不关闭窗口
echo [2/4] 正在启动 FastAPI 后端...
start "FastAPI Backend" cmd /k "cd Backend && uvicorn main:app --reload"

:: 4. 启动前端 (新建一个窗口，保留运行)
echo [3/4] 正在启动 Vue 前端...
start "Vue Frontend" cmd /k "cd Frontend && npm run dev"

:: 5. 等待几秒钟，让服务先跑起来，防止浏览器打开时报错
echo [4/4] 等待服务启动，即将打开浏览器...
timeout /t 5 >nul

:: 6. 打开浏览器访问前端页面
start http://localhost:5173

:: (可选) 打开 FastAPI 自带的接口文档，方便调试
start http://127.0.0.1:8000/docs

echo ========================================================
echo               启动完成！开心写代码吧！
echo ========================================================
:: 这里的 pause 只是为了让你看一眼上面的提示，不需要可以删掉