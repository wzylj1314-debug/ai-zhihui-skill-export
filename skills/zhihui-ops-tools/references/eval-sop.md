## 5. eval 回归 SOP

### 5.1 quick 模式

quick 模式用于快速检查规则和回答质量。

```powershell
cd F:\AI智绘客服机器人\eval
node runner.js --mode quick --force
node evaluator.js --mode quick
node report-gen.js --mode quick
```

报告输出：

```text
eval/report.quick.md
```

### 5.2 agent 模式

agent 模式更接近真实 Agent 行为。

```powershell
cd F:\AI智绘客服机器人\eval
node runner.js --mode agent --force
node evaluator.js --mode agent
node report-gen.js --mode agent
```

报告输出：

```text
eval/report.agent.md
```

### 5.3 单条用例回归

如果只修改了某个问题，可先跑单条：

```powershell
cd F:\AI智绘客服机器人\eval
node runner.js --mode quick --case TC-F09-002 --force
node evaluator.js --mode quick
node report-gen.js --mode quick
```

发布前仍建议跑完整集。
