# 便携 QMD 检索

用途：让迁移后的 agent 可以使用 QMD 做知识库检索，同时不复制当前电脑上的索引、缓存和本机绝对路径。

## 设计边界

- 本目录只提供 QMD 调用封装，不携带当前电脑的 QMD 索引。
- 默认索引目录是 `skill-export/runtime/qmd`。
- 如果要使用某台电脑上已经存在的索引，必须显式设置 `ZHIHUI_QMD_INDEX_DIR`。
- 如果要重新建索引，必须显式设置 `ZHIHUI_QMD_BIN`，并确认 QMD 已安装可用。

## 环境变量

- `ZHIHUI_QMD_BIN`：QMD 可执行文件，例如 `qmd.cmd`。
- `ZHIHUI_QMD_INDEX_DIR`：QMD 的独立索引目录。
- `ZHIHUI_KB_DIR`：要检索或重建索引的知识库目录。

## 示例

```powershell
$env:ZHIHUI_QMD_BIN = "C:\Users\you\AppData\Roaming\npm\qmd.cmd"
$env:ZHIHUI_KB_DIR = "D:\skill-export\runtime\workspace\v1_0_3"
.\Rebuild-QmdIndex.ps1
.\Search-Qmd.ps1 -Query "怎么做虚拟试衣"
```

也可以直接透传 QMD 参数：

```powershell
.\Invoke-Qmd.ps1 status
.\Invoke-Qmd.ps1 search "AI 改款"
```

## 迁移边界

QMD 的本机安装、缓存、索引和配置不属于 Skill 资产本体。迁移时复制 `skill-export` 后，在新机器配置 `ZHIHUI_QMD_BIN` 并按需重建索引。
