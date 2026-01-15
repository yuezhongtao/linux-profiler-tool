# 安装说明

## 问题修复

已修复 `pyproject.toml` 中的包配置问题。

### 修复内容

**修复前（错误）：**
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/"]  # 这会导致 ModuleNotFoundError
```

**修复后（正确）：**
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/linux_profiler"]
```

---

## 安装步骤

### 方法 1: 使用 pip（开发模式）

```bash
# 1. 进入项目目录
cd /home/debian13/Documents/linux-profiler-tool

# 2. 创建虚拟环境（如果还没有）
python3 -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 卸载旧版本（如果已安装）
pip uninstall -y linux-profiler-mcp

# 5. 重新安装（开发模式）
pip install -e .

# 6. 验证安装
linux-profiler --help
```

### 方法 2: 使用 pip（生产模式）

```bash
# 1. 构建包
pip install build
python -m build

# 2. 安装构建的包
pip install dist/linux_profiler_mcp-1.0.0-py3-none-any.whl

# 3. 验证
linux-profiler --help
```

### 方法 3: 使用 uv（推荐，更快）

```bash
# 1. 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 使用 uv 安装
cd /home/debian13/Documents/linux-profiler-tool
uv pip install -e .

# 3. 验证
linux-profiler --help
```

---

## 启动服务

### STDIO 模式（默认）

```bash
linux-profiler
```

### HTTP 模式（推荐）

```bash
# Streamable HTTP（新标准）
linux-profiler --http --port 22222

# SSE 传输（传统）
linux-profiler --http --transport sse --port 22222

# 同时支持两种传输
linux-profiler --http --transport both --port 22222

# 无状态模式
linux-profiler --http --stateless --port 22222

# 自定义主机和端口
linux-profiler --http --host 0.0.0.0 --port 8080
```

---

## 验证安装

### 检查命令是否可用

```bash
which linux-profiler
# 应该输出: /path/to/.venv/bin/linux-profiler

linux-profiler --help
# 应该显示帮助信息
```

### 检查模块是否可导入

```bash
python -c "import linux_profiler; print(linux_profiler.__file__)"
# 应该输出模块路径
```

### 启动服务测试

```bash
# 启动服务（后台运行）
linux-profiler --http --port 22222 &

# 等待几秒后测试健康检查
sleep 3
curl http://localhost:22222/health

# 停止服务
pkill -f linux-profiler
```

---

## 常见问题

### 问题 1: `ModuleNotFoundError: No module named 'linux_profiler'`

**原因**: 旧的 `pyproject.toml` 配置错误

**解决**:
```bash
# 1. 拉取最新代码（包含修复）
git pull

# 2. 卸载旧版本
pip uninstall -y linux-profiler-mcp

# 3. 重新安装
pip install -e .
```

### 问题 2: 导入错误 `ImportError: cannot import name 'CPUCollector'`

**原因**: `server.py` 中使用了隐式相对导入

**解决**: 已在代码中修复（使用 `.collectors` 而不是 `collectors`）

### 问题 3: 权限错误

```bash
# 如果遇到权限问题，使用 --user 安装
pip install --user -e .
```

### 问题 4: 依赖冲突

```bash
# 清理并重新安装
pip uninstall -y linux-profiler-mcp
pip cache purge
pip install -e .
```

---

## 开发环境设置

```bash
# 1. 安装开发依赖
pip install -e ".[dev]"

# 2. 运行测试
pytest

# 3. 代码格式检查
pip install ruff
ruff check src/

# 4. 类型检查
pip install pyright
pyright src/
```

---

## 卸载

```bash
pip uninstall linux-profiler-mcp
```
