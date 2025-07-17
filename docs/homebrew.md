1. 检查本地 homebrew
  - 输入 which brew 按回车查看结果
    - 如果返回结果是 /opt/homebrew/bin/brew --> 正常
    - 如果返回是 /usr/local/bin/brew --> 先卸载，然后进行 `2. 安装 homebrew`
      - curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh -o uninstall.sh /bin/bash uninstall.sh --path=/usr/local
    - 如果返回是两行 /opt/homebrew/bin/brew 和 /usr/local/bin/brew --> 先卸载，然后进行 `3. 再次检查`
      - curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh -o uninstall.sh /bin/bash uninstall.sh --path=/usr/local
    - 如果什么都没有返回 --> 进行 `2. 安装 homebrew`

2. 安装 homebrew
  - 如果可以连外网且流量充足：
    - /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  - 如果只能连国内的网：
    - git clone --depth=1 https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/install.git brew-install && /bin/bash brew-install/install.sh && rm -rf brew-install

3. 再次检查
  - 输入 which brew 按回车查看结果
    - 返回结果应该是 /opt/homebrew/bin/brew

4. 配置环境
  - export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
  - export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
  - export HOMEBREW_API_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles/api"
  - export HOMEBREW_INSTALL_FROM_API=1
