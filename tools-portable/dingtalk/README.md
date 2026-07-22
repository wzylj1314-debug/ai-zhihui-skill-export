# 便携钉钉发送器

用途：让任意 agent 在迁移后的机器上发送钉钉 Markdown 消息。

默认行为是 dry-run，只打印要发送的 payload，不会触达钉钉。只有显式加 `--send` 才会真正发送。

## 环境变量

- `DINGTALK_WEBHOOK`：钉钉机器人 webhook。
- `DINGTALK_SECRET`：钉钉机器人加签密钥，可为空。

也可以用 `--webhook-env` 和 `--secret-env` 指定其他变量名，例如业务群、产品群分别配置。

## 示例

```powershell
python .\send_message.py --title "FAQ 审核提醒" --text "有 3 条 FAQ 待确认"
python .\send_message.py --title "FAQ 审核提醒" --text "有 3 条 FAQ 待确认" --send
```

## 迁移边界

本目录不包含 webhook、secret 或历史发送记录。迁移到其他机器后，需要在那台机器上重新配置环境变量。
