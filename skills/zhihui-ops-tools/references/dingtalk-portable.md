# Portable DingTalk Sender

Tool path:

```text
skill-export/tools-portable/dingtalk/send_message.py
```

## Default Behavior

The sender is dry-run by default. It prints the payload and does not send anything unless `--send` is passed.

## Config

- `DINGTALK_WEBHOOK`: generic webhook.
- `DINGTALK_SECRET`: optional signing secret.

Use `--webhook-env` and `--secret-env` for multiple channels.

## Examples

```powershell
python .\send_message.py --title "FAQ Reminder" --text "3 FAQ drafts need review"
python .\send_message.py --title "FAQ Reminder" --text "3 FAQ drafts need review" --send
python .\send_message.py --webhook-env DINGTALK_PRODUCT_WEBHOOK --secret-env DINGTALK_PRODUCT_SECRET --title "Product Notes" --text "今日产品反馈" --send
```

## Transfer Boundary

Never package real webhook URLs or signing secrets. Configure them on the target machine.
