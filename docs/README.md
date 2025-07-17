# 1. Ollama

### (1) 安装 Ollama 客户端
双击文件夹中的 `Ollama.dmg`，安装客户端。

### (2) 启动 Ollama 客户端
安装完成后, 双击 ollama 程序图标运行，运行成功时电脑右上角会出现羊驼图标。

### (3) 模型下载
- 将本文件夹中的 setup_ollama.sh 文件移动到本地电脑的某个文件夹，比如 `/Users/rylee` (**运行下方命令行时需要替换对应内容**)
- 打开电脑系统自带的 `Terminal` (中文名：`终端`) 软件，输入下方命令行并回车:
  - `chmod +x /Users/rylee/setup_ollama.sh && /Users/rylee/setup_ollama.sh`
  - 等待运行完成，当出现 `✅ 下载完成` 字样说明模型准备完毕

### (4) 检查结果
在 `Terminal` 中输入命令行 `ollama list` 并回车，如果显示模型 `Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M` 和 `Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M`, 说明设置成功。

<br>

# 2. Python
### (1) 安装 Python
双击文件夹中的 `python-3.11.0-macos11.pkg`，安装 Python 到本地。

### (2) 启动 Docker 客户端
- 正确安装后，将在 `Applications (应用程序)` 文件夹看到一个新的文件夹，叫做 `Python 3.11`
- 打开这个文件夹，分别双击运行以下两个文件：
  - `Install Certificates.command`
  - `Update Shell Profile.command`
  - 注：双击后会自动跳出 `Terminal` 进行运行，当 `Terminal` 中显示 `[进程已完成]` 字样说明运行完成，关掉 `Terminal` 窗口即可。

### (3) 环境配置
- 将文件夹中的 `install_python.sh` 文件移动到本地某个文件夹，比如 `/Users/rylee` (**运行下方命令行时需要替换对应内容**)
- 打开电脑系统自带的 Terminal (终端) 软件，运行下方命令行:
  - `chmod +x /Users/rylee/install_python.sh && /Users/rylee/install_python.sh`
  - 等待运行完成，当出现 `✅ 安装完成` 字样说明 Python 准备完毕，记录好提示中给出的路径，后面会用！比如 `/Users/rylee/mnemo_venv/bin/activate`

<br>

# 3. 代码
### (1) 复制代码
将文件夹中的 `mnemo_v1-0.zip` 复制到本地某个位置，比如 `/Users/rylee` (**运行下方命令行时需要替换对应内容**)

### (2) 解压缩并找到核心代码
解压缩，找到文件 `streamlit_app.py`, 并记录下路径，比如 `/Users/rylee/mnemo_v1-0/streamlit_app.py`

<br>

# 4. 启动程序
**完成前面3步之后，以后无需重复进行，每次运行程序直接从第4步开始即可!**
### (1) 保证 ollama 客户端已经启动
方法同上

### (2) 启动程序
打开电脑系统自带的 Terminal (终端) 软件，运行下方命令行 (**下面的路径务必要根据自己的情况进行替换**):
- `source /Users/rylee/mnemo_venv/bin/activate && streamlit run /Users/rylee/mnemo_v1-0/streamlit_app.py`

### (3) 程序会自动打开浏览器，开始运行
初次打开需要一点时间初始化，如果好几分钟都没有出现界面，可以刷新网页试试。

<br>

# 5. 运行程序
### (1) 初始化
- 在左侧菜单栏选择 `initialize`，填入想要保存数据的文件夹路径（不是文件位置，是根据文件创建的数据库位置），点击 `initialize` 进行数据库初始化
- 仅需要在第一次使用时初始化一次

### (2) 文件入库
- 在左侧菜单栏选择 `organize`，填入文件所在的文件夹位置，点击 `start` 开始进行文件入库。
- 每次会默认入库文件夹中的所有符合要求的文件，如果已经入库过会跳过。同个文件名但是不同文件夹的文件，会被当成一个文件，只入库一次。
- 目前阶段仅支持 `ppt` 和 `pdf` 文件（可勾选）。如果同个文件内容有 `ppt` 和 `pdf` 两个版本，建议使用 `ppt` 版本，能更准确捕捉文本内容，耗时也相对更短。
- 建议一次性不要入库过多文件，以免一次耗时过长。
  - 如果左侧 `Chooose LLM model` 菜单选择 `quality`，会启用较大模型，准确度更高，但每个文件耗时1-2分钟（取决于机器性能）
  - 如果左侧 `Chooose LLM model` 菜单选择 `speed`，会启用较小模型，准确度降低，每个文件耗时1分钟内（取决于机器性能）
  - 经过测试，一般来说建议使用 `quality` 模型
- 第一次入库可以选择几个文件进行测试，看是否有任何问题出现
- 如果在运行过程中想临时终止，可点击左侧菜单的 `Stop` 按钮

### (3) 文件搜索
- 在左侧菜单栏选择 `search`，填入你想搜索的内容即可

### (4) 使用完后关闭
- 关闭网页
- 退出 ollama 客户端
- 在运行 `source /Users/rylee/mnemo_venv/bin/activate && streamlit run /Users/rylee/mnemo_v1-0/streamlit_app.py` 的 `Terminal` 窗口 ，CTRL+C 终止进程